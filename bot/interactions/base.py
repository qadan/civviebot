'''
Interaction components to use with the 'base' cog.
'''

import logging
from discord import ComponentType, Interaction
from pony.orm import db_session, ObjectNotFound
from bot.interactions.common import ChannelAwareSelect
from database.models import GuildSettings
from utils.utils import get_discriminated_name, handle_callback_errors


class SelectPermissionRoles(ChannelAwareSelect):
    '''
    Select for setting roles for permissions.

    These will be passed different custom_ids for the eventual callback.
    '''

    def __init__(self, tracked_perm: str, *args, **kwargs):
        '''
        Constructor; the 'tracked_perm' option should reference a Set(int) column in the
        GuildSettings table.
        '''
        if not hasattr(GuildSettings, tracked_perm):
            raise ValueError((f'Permission "{tracked_perm}" is not valid; must be a tracked '
                'setting in the GuildSettings table.'))
        self._tracked_perm = tracked_perm
        kwargs['select_type'] = ComponentType.role_select
        kwargs['max_values'] = 25
        super().__init__(*args, **kwargs)

    @property
    def tracked_perm(self) -> str:
        '''
        The column in the GuildSettings table this is tracking.
        '''
        return self._tracked_perm

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback; updates the permissions.
        '''
        guild = self.bot.get_channel(self.channel_id).guild
        with db_session():
            try:
                guild_settings = GuildSettings[str(guild.id)]
            except ObjectNotFound:
                logging.warn(('Guild %d was missing GuildSettings in the database; creating a new '
                    'column ...'))
                guild_settings = GuildSettings(guildid=str(guild.id))
            values = [role.id for role in self.values]
            setattr(guild_settings, self.tracked_perm, values)
            vals_to_string = ', '.join([f'{role.name} ({role.id})' for role in self.values])
            logging.info('User %s set the "%s" permission for guild %d to roles: %s',
                get_discriminated_name(interaction.user),
                self.tracked_perm,
                guild.id,
                vals_to_string)
        interaction.response.send_message(
            content=f'Set the "{self.tracked_perm}" permissions to the roles: {vals_to_string}',
            ephemeral=True)