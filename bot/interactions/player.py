'''
Interaction components to use with the 'player' cog.
'''

import logging
from typing import List
from discord import ComponentType, Interaction, User
from discord.components import SelectOption
from discord.ext.commands import Bot
from pony.orm import db_session, left_join, ObjectNotFound
from bot.interactions.common import ChannelAwareSelect, View, SelectGame
from database.models import Player, Game
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
            player = Player[self.player_id]
            if player.discordid:
                await interaction.response.edit_message(
                    content=('Sorry, it looks like this user is already linked to a Discord user; '
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

    def __init__(self, *args, target_user: User = None, **kwargs):
        '''
        Constructor; establishes the player information.
        '''
        self._player_id = None
        self._target_user = target_user
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
    def target_user(self) -> User | None:
        '''
        The user who created this element.

        If not None, this interaction is expected to directly target that user. Otherwise, this
        interaction should follow up to ask for a user if necessary.
        '''
        return self._target_user

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
                    content=('Sorry, it looks like this user is already linked to a Discord user; '
                        'likely this happened while you were picking it.'))
                return
            player.discordid = str(self.target_user.id)
            if self.target_user:
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

    @db_session
    def get_player_options(self) -> List[SelectOption]:
        '''
        Override the player options to limit to the initiating user if necessary.
        '''
        if self.target_user:
            results = left_join(p for p in Player for g in p.games if
                g.webhookurl.channelid == self.channel_id and
                p.discordid == self.target_user.id)
            return [self.get_player_as_option(result) for result in results]
        return super().get_player_options()

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        with db_session():
            player = Player[self.player_id]
            existing_user = player.discordid
            player.discordid = ''

        logger.info(
            'Removed the link between player %s and Discord user %s',
            player.playername,
            existing_user)
        await interaction.response.edit_message(
            content=f'The link to {player.playername} has been removed.',
            view=None)

class UnlinkUserSelect(PlayerSelect):
    '''
    Provides a select that allows for unlinking of a user's player links.
    '''

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback; removes the link to the target_user.
        '''
        with db_session():
            player = Player[self.player_id]
            player.discordid = ''
        await interaction.response.edit_message(
            content=f'The link between you and {player.playername} has been removed.',
            view=None)

    @db_session()
    def get_player_options(self) -> List[SelectOption]:
        '''
        Gets the list of players that can be unlinked from the user as an SelectOption list.
        '''
        return [self.get_player_as_option(player) for player in left_join(
            p for p in Player for g in p.games if
            g.webhookurl.channelid == self.channel_id
            and p.discordid == self.target_user.id)]

class SelectGameForPlayers(SelectGame):
    '''
    Select menu including a callback to refresh the player select view.
    '''

    def __init__(
        self,
        player_select: PlayerSelect,
        channel_id: int,
        bot: Bot,
        *args,
        target_user: User = None,
        **kwargs):
        '''
        Constructor; accepts the PlayerSelect component this component should combo into.
        '''
        self._player_select = player_select
        self._target_user = target_user
        super().__init__(channel_id, bot, *args, **kwargs)

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback; updates the message content and changes the view to the provided PlayerSelect.
        '''
        with db_session():
            game = Game[self.game_id]
        await interaction.response.edit_message(
            content=f"Select a player that's being tracked in **{game.gamename}**:",
            view=View(self.player_select))

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handling, in particular if we fail to find the selected game.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(('Sorry, the game you selected appears to no '
                'longer exist. Was it deleted before you were able to select it?'),
            view=None)
            return
        await super().on_error(error, interaction)

    @property
    def player_select(self) -> PlayerSelect:
        '''
        The PlayerSelect component this component combos into.
        '''
        return self._player_select

    @property
    def target_user(self) -> User:
        '''
        The user that initiated the request that created this component.
        '''
        return self._target_user

class SelectGameForLinkedPlayers(SelectGameForPlayers):
    '''
    Select menu to choose games containing players the initiating user is linked to.
    '''

    @db_session
    def get_game_options(self) -> List[SelectOption]:
        '''
        Gets a List of SelectOption objects.
        '''
        if self.target_user:
            return [self.get_game_as_option(game) for game in left_join(
                g for g in Game for p in g.players if
                g.webhookurl.channelid == str(self.channel_id) and
                p.discordid == self.target_user.id)]
        return super().get_game_options()

class SelectGameForUnlinkedPlayers(SelectGameForPlayers):
    '''
    Select menu to choose games containing unlinked players.
    '''

    @db_session
    def get_game_options(self) -> List[SelectOption]:
        '''
        Gets a List of SelectOption objects.
        '''
        return [self.get_game_as_option(game) for game in left_join(
            g for g in Game for p in g.players if
            g.webhookurl.channelid == str(self.channel_id) and
            p.discordid == '')]
