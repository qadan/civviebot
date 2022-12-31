'''
Components that are not abstract but are still used between cogs.
'''

from datetime import datetime
import logging
from typing import List
from discord import Interaction
from discord.components import SelectOption
from discord.ui import Modal, Select, InputText, Button
import discord.ui.view as core_view
from discord.ext.commands import Bot
from pony.orm import db_session
from database.models import Game
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

    def __init__(self, *args, notify_interval: int = None, **kwargs):
        '''
        The notify interval to set. Will get the global config if not passed in.
        '''
        if kwargs.get('value', None) is None:
            kwargs['value'] = (config.get('stale_notification_length') if notify_interval is None
            else str(notify_interval))
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
            kwargs['value'] = config.get('min_turns') if min_turns is None else str(min_turns)
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

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Base on_error implementation if needed.
        '''
        await base_error(logger, error, interaction)

class GameAwareButton(Button):
    '''
    Button component that stores a game_id.
    '''

    def __init__(self, game_id: int, *args, **kwargs):
        '''
        Constructor; sets the game_id, channel_id and bot.
        '''
        self._game_id = game_id
        super().__init__(*args, **kwargs)

    @property
    def game_id(self) -> int:
        '''
        The ID of the game this button is tracking.
        '''
        return self._game_id

class SelectGame(ChannelAwareSelect):
    '''
    Represents a select list for the games attached to the given channel_id.

    Does not include a callback.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor; sets the options from games found via the channelid.
        '''
        self._game_id = None
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
        try:
            user = self.bot.get_user(int(game.lastup.discordid))
            name = get_discriminated_name(user) if user else game.lastup.playername
        # From game.lastup.discordid being an empty string.
        except ValueError:
            name = game.lastup.playername
        lastturn = datetime.now() - datetime.fromtimestamp(game.lastturn)
        desc = f"{name}'s turn ({expand_seconds_to_string(lastturn.total_seconds())} ago)"
        return SelectOption(
            label=game.gamename,
            value=str(game.id),
            description=desc)

    @db_session
    def get_game_options(self) -> List[SelectOption]:
        '''
        Gets a List of SelectOption objects for the games that should be provided as options.
        '''
        return [self.get_game_as_option(game) for game in
            Game.select(lambda g: g.webhookurl.channelid == str(self.channel_id))]

    @property
    def game_id(self) -> int:
        '''
        Getter for the game_id property.
        '''
        try:
            game_id = int(self.values[0])
        except IndexError as error:
            raise ValueAccessError('Attempting to access game before it was set') from error
        except ValueError as error:
            raise ValueAccessError(
                'Tried to access game but it cannot be cast to an integer') from error
        return game_id
