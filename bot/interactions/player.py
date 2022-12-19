'''
Interaction components to use with the 'player' cog.
'''

import logging
from typing import List
from discord import ComponentType, Interaction, User, Embed
from discord.ui import View
from discord.components import SelectOption
from pony.orm import db_session, left_join, ObjectNotFound
from bot.interactions.common import ChannelAwareSelect, ChannelAwareModal
from database.models import Player
from utils.errors import ValueAccessError
from utils.utils import get_discriminated_name, handle_callback_errors, pluralize


SELECT_FAILED = ('An error occurred and CivvieBot was unable to get the selected option(s). '
    "Please try again later, and if this persists, contact CivvieBot's author.")


class NoPlayersError(ValueError):
    '''
    Error to throw when players can't be found.
    '''


class LinkUserSelect(ChannelAwareSelect):
    '''
    Select menu for a user to link to a previously selected player.

    Uses custom_id 'user_select'.
    '''

    def __init__(self, player_id: int, *args, **kwargs):
        '''
        Constructor; establishes the user property and sets the component type to user_select.
        '''
        self._user = None
        self._player_id = player_id
        kwargs['select_type'] = ComponentType.user_select
        super().__init__(custom_id='user_select', *args, **kwargs)


    @property
    def user(self) -> User:
        '''
        The selected user.
        '''
        try:
            self._user = self.bot.get_user(int(self.values[0]))
        except IndexError as error:
            raise ValueAccessError('Attempting to access user before it was set.') from error
        except ValueError as error:
            raise ValueAccessError(
                'Tried to access user but it cannot be cast to an integer.') from error
        return self._user


    @property
    def player_id(self) -> int:
        '''
        The ID of the player that the selected user will be linked to.
        '''
        return self._player_id


    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback; handles the actual linking.
        '''
        with db_session():
            player_id = getattr(
                next(filter(lambda c: c.custom_id == 'player_select', self.children)),
                'player_id')
            player = Player[player_id]
            if player.discordid:                
                await interaction.response.edit_message(
                    content=(f'Sorry, it looks like this user is already linked to a Discord user; '
                        'likely this happened while you were picking it.'))
                return
            player.discordid = self.user.id
            logging.info(
                'Set the Discord ID of %s (%d) to %d (channel: %d)',
                player.playername,
                player.id,
                self.user.id,
                interaction.channel_id)


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for player/user link.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.send_message(
                ('Failed to find the selected player; was it removed before the link could be '
                    'created?'))
            return
        super().on_error(error, interaction)


class PlayerSelect(ChannelAwareSelect):
    '''
    Select menu for choosing a player being tracked in a given channel.

    Uses custom_id 'player_select'.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor; establishes the player information.
        '''
        self._player_id = None
        super().__init__(
            custom_id='player_select',
            placeholder='Select a player',
            *args,
            **kwargs)
        self.options = self.get_player_options()
        if not self.options:
            raise NoPlayersError('No players could be added to the options list')


    @db_session
    def get_player_as_option(self, player: Player) -> SelectOption:
        '''
        Returns a Player formatted as a SelectOption.
        '''
        print(player)
        return SelectOption(
            label=player.playername,
            value=str(player.id),
            description=(f'In {len(player.games)} {pluralize("game", player.games)} (up in '
                f'{len(player.upin)})'))


    @db_session
    def get_player_options(self) -> List[SelectOption]:
        '''
        Gets a List containing the Players in this channel as SelectOptions
        '''
        results = left_join(p for p in Player for g in p.games if
            g.webhookurl.channelid == self.channel_id)
        return [self.get_player_as_option(player) for player in results]


    @property
    def player_id(self) -> int:
        '''
        Getter for the player. Attempts to get the player ID from self.values.
        '''
        if not self._player_id:
            try:
                self._player_id = int(self.values[0])
            except IndexError as error:
                raise ValueAccessError('Attempting to access player before it was set.') from error
            except ValueError as error:
                raise ValueAccessError(
                    'Tried to access player but it cannot be cast to an integer.') from error
        return self._player_id


class LinkedPlayerSelect(PlayerSelect):
    '''
    Select menu for choosing a player in a given channel that is currently linked to a user.
    '''

    @db_session
    def get_player_as_option(self, player: Player) -> SelectOption:
        try:
            user = self.bot.get_user(int(player.discordid))
            if user:
                desc = f'Linked to {get_discriminated_name(user)}'
            else:
                desc = 'Unable to load linked user'
        except ValueError:
            desc = 'No longer appears to be linked'
        return SelectOption(
            label=player.playername,
            value=str(player.id),
            description=desc)


    @db_session
    def get_player_options(self) -> List[SelectOption]:
        '''
        Gets all players currently linked to a user in this channel as SelectOptions
        '''
        results = left_join(p for p in Player for g in p.games if
            g.webhookurl.channelid == self.channel_id and
            p.discordid != '')
        return [self.get_player_as_option(result) for result in results]


class UnlinkedPlayerSelect(PlayerSelect):
    '''
    Select menu for choosing a player who is not currently linked to a user.
    '''

    @db_session
    def get_player_options(self) -> List[SelectOption]:
        '''
        Gets all players currently not linked to a user in this channel as SelectOptions
        '''
        results = left_join(p for p in Player for g in p.games if
            g.webhookurl.channelid == self.channel_id and
            p.discordid == '')
        return [self.get_player_as_option(result) for result in results]


    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback; re-renders the response to provide the user select.
        '''
        with db_session():
            player = Player[self.player_id]
        if player.discordid:
            await interaction.response.edit_message(
                content=(f'Sorry, it looks like this user is already linked to a Discord user; '
                    'likely this happened while you were picking it.'))
            return
        await interaction.response.edit_message(
            content=f'Select the user you would like to link to {player.playername}:',
            view=View(LinkUserSelect(player.id, self.channel_id, self.bot)))


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for a missing player.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content=('Failed to find the selected player; was it removed before the link could be '
                    'created?'))
        await super().on_error(error, interaction)


class UnlinkPlayerSelect(LinkedPlayerSelect):
    '''
    Class containing callback to remove the user link from the given player.
    '''

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        with db_session():
            player = Player[self.player_id]
            existing_user = player.discordid
            player.discordid = ''

        logging.info(
            'Removed the link between player %s (%d) and Discord ID %s',
            player.name,
            player.value,
            existing_user)
        await interaction.response.edit_message(
            content=f'The link between player {player.name} and its Discord user has been removed.')


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for player link removal.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.send_message(
                content=('Unable to remove the link from this player as this player does not have '
                    'a link. Was it already removed?'))
        await super().on_error(error, interaction)


class UserLinkedPlayersSelect(PlayerSelect):
    '''
    Provides a drop-down menu to select one or more linked players.
    '''

    def __init__(self, user: User, *args, **kwargs):
        self._player_ids = None
        self._user = user
        del kwargs['user']
        kwargs['max_values'] = 25
        super().__init__(*args, **kwargs)


    @db_session
    def get_player_options(self) -> List[SelectOption]:
        '''
        Gets a List containing the Players in this channel as SelectOptions
        '''
        results = left_join(p for p in Player for g in p.games if
            g.webhookurl.channelid == self.channel_id and
            p.discordid == str(self.user.id))
        return [self.get_player_as_option(player) for player in results]


    @property
    def user(self) -> User:
        '''
        Getter for the user.
        '''
        return self._user


class UnlinkUserModal(ChannelAwareModal):
    '''
    Provides a modal that allows for multi-select unlinking of a user's player links.
    '''

    def __init__(self, user: User, *args, **kwargs):
        '''
        Constructor; adds in the UserLinkedPlayersSelect.
        '''
        del kwargs['user']
        super().__init__(
            UserLinkedPlayersSelect(
                channel_id=kwargs['channel_id'],
                bot=kwargs['bot'],
                user=user),
            *args,
            **kwargs)


    async def callback(self, interaction: Interaction):
        '''
        Interaction callback; removes the links from the selected players.
        '''
        users = self.get_child_value('user_select')
        embed = Embed(
            title='Unlinked players',
            description='Links removed from the following players:')
        with db_session():
            for user_id in users:
                for player in left_join(p for p in player for g in p.games if
                    p.discordid == user_id and g.webhookurl.channelid == self.channel_id):
                    player.discordid = ''
                    logging.info(
                        'User %s removed the link between player %s (%d) and Discord ID %d',
                        get_discriminated_name(interaction.user),
                        player.playername,
                        player.id,
                        user_id)
                    embed.add_field(
                        name=player.playername,
                        value=f'Link removed from {get_discriminated_name(user_id)}')
        await interaction.response.edit_message(content='', embed=embed)
