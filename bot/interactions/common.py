'''
Components that are not abstract but are still used between cogs.
'''

import logging
from traceback import format_list, extract_tb
from discord import Interaction, ButtonStyle
from discord.errors import HTTPException, Forbidden
from discord.ui import Modal, Select, InputText, Button
import discord.ui.view as core_view
from discord.ext.commands import Bot
from utils import config
from utils.errors import ValueAccessError

logger = logging.getLogger(f'civviebot.{__name__}')


class View(core_view.View):
    '''
    View class with an overridden timeout.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor that forces the view timeout to None.
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
            else notify_interval)
        if kwargs.get('label', None) is None:
            kwargs['label'] = 'Seconds between re-pings (use 0 to disable):'
        super().__init__(custom_id='notify_interval', *args, **kwargs)

    @property
    def value(self) -> int | None:
        '''
        Overriding the value property to provide None on falsy, including 0
        '''
        if self._input_value is not False:
            return self._input_value if self._input_value else None
        return self._underlying.value


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
            kwargs['value'] = config.get('min_turns') if min_turns is None else min_turns
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

        Outside of the interaction, the log is intended to mimic other on_error implementations in
        py-cord.
        '''
        logger.error(
            'Unexpected failure in ChannelAwareSelect: %s: %s\n%s',
            error.__class__.__name__,
            error,
            ''.join(format_list(extract_tb(error.__traceback__))))
        await interaction.response.edit_message(
            content=('An unknown error occurred; contact an administrator if this persists.'))


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


class CancelButton(Button):
    '''
    Deletes the original message.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor; sets the label and style.
        '''
        kwargs['label'] = 'Cancel'
        kwargs['style'] = ButtonStyle.grey
        super().__init__(*args, **kwargs)


    async def callback(self, interaction: Interaction):
        '''
        Callback to delete the original message.
        '''
        try:
            await interaction.delete_original_response()
        except (HTTPException, Forbidden):
            pass
        try:
            await interaction.delete_original_message()
        except (HTTPException, Forbidden):
            pass
