'''
Components that are not abstract but are still used between cogs.
'''

import logging
from datetime import datetime
from typing import List
from discord import Interaction
from discord.components import SelectOption
from discord.ui import Modal, Select, InputText, Button
import discord.ui.view as core_view
from discord.ext.commands import Bot
from sqlalchemy import select, func
from sqlalchemy.exc import NoResultFound
from database.models import Game, TurnNotification, WebhookURL
from database.utils import get_session, get_url_for_channel
from utils import config
from utils.errors import ValueAccessError, NoGamesError, base_error
from utils.utils import expand_seconds_to_string, get_discriminated_name

logger = logging.getLogger(f'civviebot.{__name__}')

class View(core_view.View):
    '''
    View class with overridden timeout parameters.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor that forces view timeout to None.
        '''
        kwargs['timeout'] = None
        super().__init__(*args, **kwargs)

class NotifyIntervalInput(InputText):
    '''
    Input text for setting a game's notify interval.

    Uses custom_id 'notify_interval'.
    '''

    def __init__(self, *args, remind_interval: int = None, **kwargs):
        '''
        The notify interval to set. Will get the global config if not passed in.
        '''
        if kwargs.get('value', None) is None:
            kwargs['value'] = str(config.REMIND_INTERVAL if remind_interval is None
            else remind_interval)
        if kwargs.get('label', None) is None:
            kwargs['label'] = 'Seconds between re-pings (use 0 to disable):'
        kwargs['custom_id'] = 'notify_interval'
        super().__init__(*args, **kwargs)

class MinTurnsInput(InputText):
    '''
    Input text for setting a game's minimum turns.

    Uses custom_id 'min_turns'.
    '''

    def __init__(self, *args, min_turns: int = None, **kwargs):
        '''
        The minimum turns to set. Will get the global config if not passed in.
        '''
        if kwargs.get('value', None) is None:
            kwargs['value'] = config.MIN_TURNS if min_turns is None else str(min_turns)
        if kwargs.get('label', None) is None:
            kwargs['label'] = 'Start notifying after turn:'
        super().__init__(custom_id='min_turns', *args, **kwargs)

class ChannelAwareModal(Modal):
    '''
    A component that stores a channel_id and bot.
    '''

    def __init__(self, channel_id: int, bot: Bot, *args, **kwargs):
        '''
        Constructor; sets the channel_id and bot.
        '''
        self._channel_id = channel_id
        self._bot = bot
        super().__init__(*args, **kwargs)

    @property
    def channel_id(self) -> int:
        '''
        The channel this URL interaction was initiated from.
        '''
        return self._channel_id

    @property
    def bot(self) -> Bot:
        '''
        Instance of CivvieBot passed in from the interaction.
        '''
        return self._bot

    def get_child_value(self, custom_id: str):
        '''
        Gets the value of a child component by its custom_id.

        Manually set the custom_id of a child component in order to find it using this.
        '''
        try:
            component = next(filter(lambda c: c.custom_id == custom_id, self.children))
        except StopIteration as error:
            raise IndexError(
                f'Accessed a non-existent component by custom_id {custom_id}') from error
        if component.value is None:
            raise ValueAccessError(
                f'Accessed value of component by custom_id {custom_id} before it was set')
        return component.value

class ChannelAwareSelect(Select):
    '''
    A component that stores a channel_id and bot.
    '''

    def __init__(self, channel_id: int, bot: Bot, *args, **kwargs):
        '''
        Subclass constructor hook; sets the channel_id and bot.
        '''
        self._url = None
        self._generated = False
        self._channel_id = channel_id
        self._bot = bot
        super().__init__(*args, **kwargs)

    @property
    def channel_id(self) -> int:
        '''
        The ID of the channel this URL interaction was initiated in.
        '''
        return self._channel_id

    @property
    def bot(self) -> Bot:
        '''
        The Discord bot.
        '''
        return self._bot

    @property
    def url(self) -> WebhookURL:
        '''
        The WebhookURL for this channel.

        If a WebhookURL has not yet been generated for this channel, one will be created.
        '''
        if not self._url:
            self._url = get_url_for_channel(self.channel_id)
        return self._url

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Base on_error implementation if needed.
        '''
        await base_error(logger, error, interaction)

class GameAwareButton(Button):
    '''
    Button component that stores a Game.
    '''

    def __init__(self, game: Game, *args, **kwargs):
        '''
        Constructor; sets the game_id, channel_id and bot.
        '''
        self._game = game
        super().__init__(*args, **kwargs)

    @property
    def game(self) -> Game:
        '''
        The game this button is tracking.
        '''
        return self._game

class SelectGame(ChannelAwareSelect):
    '''
    Represents a select list for the games attached to the given channel_id.

    Does not include a callback.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor; sets the options from games found via the channelid.
        '''
        self._game = None
        super().__init__(
            custom_id='select_game',
            placeholder='Select a game',
            *args,
            **kwargs)
        self.options = self.get_game_options()
        if not self.options:
            raise NoGamesError('No options found for games.')

    def get_game_as_option(self, game: Game) -> SelectOption:
        '''
        Converts a Game object to a SelectOption.
        '''
        with get_session() as session:
            current_turn = session.scalar(select(TurnNotification)
                .join(TurnNotification.game, TurnNotification.game == game)
                .where(func.max(TurnNotification.logtime))
                .where(TurnNotification.game == game))
        if current_turn.player.discordid:
            user = self.bot.get_user(current_turn.player.discordid)
            name = get_discriminated_name(user) if user else current_turn.player.name
        else:
            name = current_turn.player.name
        delta_seconds = (datetime.now() - current_turn.logtime).total_seconds()
        return SelectOption(
            label=game.name,
            value=game.name,
            description=f"{name}'s turn ({expand_seconds_to_string(delta_seconds)} ago)")

    def get_game_options(self) -> List[SelectOption]:
        '''
        Gets a List of SelectOption objects for the games that should be provided as options.
        '''
        with get_session() as session:
            games = session.scalars(select(Game).join(Game.webhookurl).where(
                WebhookURL.channelid == self.channel_id))
            return [self.get_game_as_option(game) for game in games.all()]

    @property
    def game(self) -> Game:
        '''
        Getter for the game_id property.
        '''
        try:
            self._game = int(self.values[0])
        except IndexError as error:
            raise ValueAccessError('Attempting to access game before it was set') from error
        except ValueError as error:
            raise ValueAccessError(
                'Tried to access game but it cannot be cast to an integer') from error
        with get_session() as session:
            game =session.scalar(select(Game).join(Game.webhookurl).where(
                Game.name == self._game
                and WebhookURL.channelid == self.channel_id))
        if not game:
            raise NoResultFound('Tried to access game but it could not be found in the database')
        return game

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Base on_error implementation that reports a game could not be found.
        '''
        if isinstance(error, NoResultFound):
            await interaction.response.edit_message(
                content=('Failed to find the selected game; was it removed before you could get '
                    'the player list?'),
                embed=None)
            return
        await super().on_error(error, interaction)
