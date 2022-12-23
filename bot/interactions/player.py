'''
Interaction components to use with the 'player' cog.
'''

import logging
from typing import List
from discord import ComponentType, Interaction, User
from discord.components import SelectOption
from discord.ext.commands import Bot
from pony.orm import db_session, left_join, ObjectNotFound
from bot.interactions.common import ChannelAwareSelect, View
from database.models import Player
from utils.errors import ValueAccessError, NoPlayersError
from utils.utils import get_discriminated_name, handle_callback_errors, pluralize

logger = logging.getLogger(f'civviebot.{__name__}')

SELECT_FAILED = ('An error occurred and CivvieBot was unable to get the selected option(s). '
    "Please try again later, and if this persists, contact CivvieBot's author.")


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
            logger.info(
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

    def __init__(self, *args, initiating_user: User = None, **kwargs):
        '''
        Constructor; establishes the player information.
        '''
        self._player_id = None
        self._initiating_user = initiating_user
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
        return SelectOption(
            label=player.playername,
            value=str(player.id),
            description=(f'In {pluralize("game", player.games)} (up in {len(player.upin)})'))


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
        try:
            self._player_id = int(self.values[0])
        except IndexError as error:
            raise ValueAccessError('Attempting to access player before it was set.') from error
        except ValueError as error:
            raise ValueAccessError(
                'Tried to access player but it cannot be cast to an integer.') from error
        return self._player_id


    @property
    def initiating_user(self) -> User | None:
        '''
        The user who created this element.

        If not None, this interaction is expected to directly target that user. Otherwise, this
        interaction should follow up to ask for a user if necessary.
        '''
        return self._initiating_user
    

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Base on_error handler for failing to load the player.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content=('Failed to find the user you selected; was it deleted before you could '
                    'select it?'))
        await super().on_error(error, interaction)


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
        Gets all players currently not linked to a user in this channel as SelectOptions.
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
            if self.initiating_user:
                player.discordid = str(self.initiating_user.id)
                await interaction.response.edit_message(
                    content=(f'You have been linked to {player.playername}; you will be directly '
                        "pinged on that player's future turns."),
                    view=None)
                return
        await interaction.response.edit_message(
            content=f'Select the user you would like to link to {player.playername}:',
            view=View(LinkUserSelect(player.id, self.channel_id, self.bot)))


class UnlinkPlayerSelect(LinkedPlayerSelect):
    '''
    Class containing callback to remove the user link from the given player.
    '''

    def get_player_options(self) -> List[SelectOption]:
        '''
        Override the player options to limit to the initiating user if necessary.
        '''
        if self.initiating_user:            
            results = left_join(p for p in Player for g in p.games if
                g.webhookurl.channelid == self.channel_id and
                p.discordid == self.initiating_user.id)
            return [self.get_player_as_option(result) for result in results]
        return super().get_player_options()


    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        with db_session():
            player = Player[self.player_id]
            existing_user = player.discordid
            player.discordid = ''

        logger.info(
            'Removed the link between player %s (%d) and Discord ID %s',
            player.name,
            player.value,
            existing_user)
        await interaction.response.edit_message(
            content=f'The link between player {player.name} and its Discord user has been removed.')


class UserLinkedPlayerSelect(PlayerSelect):
    '''
    Provides a drop-down menu to select a player linked to the initiating user.
    '''

    @db_session
    def get_player_options(self) -> List[SelectOption]:
        '''
        Gets a List containing the linked Players in this channel as SelectOptions
        '''
        results = left_join(p for p in Player for g in p.games if
            g.webhookurl.channelid == self.channel_id and
            p.discordid == str(self.initiating_user.id))
        return [self.get_player_as_option(player) for player in results]
    
    
    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Interaction callback; removes the links from the selected players.
        '''
        with db_session():
                for player in left_join(p for p in Player for g in p.games if
                    p.discordid == self.initiating_user.id and
                    g.webhookurl.channelid == self.channel_id):
                    player.discordid = ''
                    unlinked_user = get_discriminated_name(self.initiating_user)
                    logger.info(
                        'User %s removed the link between player %s (%d) and Discord ID %d',
                        get_discriminated_name(interaction.user),
                        player.playername,
                        player.id,
                        unlinked_user)
        await interaction.response.edit_message(
            content=f'Link to {player.playername} removed from {unlinked_user}')


class UnlinkUserSelect(PlayerSelect):
    '''
    Provides a select that allows for unlinking of a user's player links.
    '''

    def __init__(self, channel_id: int, bot: Bot, *args, **kwargs):
        '''
        Constructor; adds in the UserLinkedPlayerSelect.
        '''
        if 'initiating_user' not in kwargs or kwargs['initiating_user'] == None:
            raise ValueError('UnlinkUserSelect must be called with an initiating_user')
        super().__init__(
            UserLinkedPlayerSelect(
                channel_id,
                bot,
                initiating_user=kwargs['initiating_user']),
                *args,
                **kwargs)
    

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback; removes the link to the initiating_user.
        '''
        with db_session():
            player = Player[self.player_id]
            player.discordid = None
        interaction.response.edit_message(
            content=f'The link between you and {player.playername} has been removed.')