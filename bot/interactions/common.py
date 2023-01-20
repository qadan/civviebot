'''
Components that are not abstract but are still used between cogs.
'''

import logging
from discord.ui import Modal, InputText, Button
import discord.ui.view as core_view
from discord.ext.commands import Bot
from database.models import Game
from utils import config
from utils.errors import ValueAccessError


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
        The notify interval to set. Will be the global config if not passed in.
        '''
        if kwargs.get('value', None) is None:
            kwargs['value'] = str(
                config.REMIND_INTERVAL
                if remind_interval is None
                else remind_interval
            )
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
            kwargs['value'] = (
                config.MIN_TURNS
                if min_turns is None
                else str(min_turns)
            )
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
        '''
        try:
            component = next(
                filter(lambda c: c.custom_id == custom_id, self.children)
            )
        except StopIteration as error:
            raise IndexError(
                f'Accessed a non-existent component by custom_id {custom_id}'
            ) from error
        if component.value is None:
            raise ValueAccessError(
                (
                    f'Accessed value of component by custom_id {custom_id} '
                    'before it was set'
                )
            )
        return component.value


class GameAwareButton(Button):
    '''
    Button component that stores a Game.
    '''

    def __init__(self, game: Game, *args, **kwargs):
        '''
        Constructor; sets the game_id, channel_id and bot.
        '''
        self._game = game.id
        self._channel_id = game.webhookurl.channelid
        super().__init__(*args, **kwargs)

    @property
    def game(self) -> int:
        '''
        The game this button is tracking.
        '''
        return self._game

    @property
    def channel_id(self) -> int:
        '''
        The channel this button is in.
        '''
        return self._channel_id
