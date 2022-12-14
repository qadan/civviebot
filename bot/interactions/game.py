'''
Interaction components to use with the 'game' cog.
'''

import logging
from datetime import datetime
from time import time
from typing import List
from discord import SelectOption, Interaction
from pony.orm import db_session
from bot.messaging import game as game_messaging
from bot.messaging import notify as notify_messaging
from bot.interactions.common import (MinTurnsInput,
    NotifyIntervalInput,
    ChannelAwareModal,
    ChannelAwareSelect)
from database.models import Game
from utils.errors import ValueAccessError
from utils.utils import get_discriminated_name, expand_seconds_to_string, handle_callback_errors

GAME_SELECT_FAILED = ('An error occurred and CivvieBot was unable to get the selected game. '
    "Please try again later, and if this persists, contact CivvieBot's author.")

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
        Gets a List of SelectOption objects
        '''
        return [self.get_game_as_option(game) for game in
            Game.select(lambda g: g.webhookurl.channelid == str(self.channel_id))]


    @property
    def game_id(self) -> int:
        '''
        Getter for the game_id property.
        '''
        if not self._game_id:
            try:
                game_id = int(self.values[0])
            except IndexError as error:
                raise ValueAccessError('Attempting to access game before it was set') from error
            except ValueError as error:
                raise ValueAccessError(
                    'Tried to access game but it cannot be cast to an integer') from error
        return game_id


class SelectGameForInfo(SelectGame):
    '''
    SelectGame drop-down for getting info about a game.
    '''

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback for a user selecting a game from the drop-down to get info about.
        '''
        await interaction.response.send_message(
            embed=game_messaging.get_game_info_embed(game_id=self.game_id, bot=self.bot),
            ephemeral=True)


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for getting information.
        '''
        match error.__class__.__name__:
            case 'ObjectNotFound':
                await interaction.response.send_message(
                    ('Failed to get information about the given game; was it removed before you '
                        'were able to get information about it?'),
                    ephemeral=True)
            case _:
                logging.error(
                    'Unexpected error while trying to get info for game %s: %s',
                    self.game_id,
                    error)
                await interaction.response.send_message(GAME_SELECT_FAILED, ephemeral=True)


class SelectGameForEdit(SelectGame):
    '''
    SelectGame drop-down for editing a game.
    '''

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback for a user selecting a game from the drop-down to edit.

        Edits the original message, adding in (or modifying) fields and a button for editing.
        '''
        with db_session():
            game = Game[self.game_id]
        await interaction.response.send_modal(GameEditModal(
            self.game_id,
            self.channel_id,
            self.bot,
            NotifyIntervalInput(notify_interval=game.notifyinterval),
            MinTurnsInput(min_turns=game.minturns),
            title=f'Editing information about {game.gamename}'))


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for editing a game.
        '''
        match error.__class__.__name__:
            case 'ValueAccessError' | 'IndexError':
                await interaction.response.send_message(GAME_SELECT_FAILED, ephemeral=True)
            case 'ObjectNotFound':
                await interaction.response.send_message(
                    ('Failed to edit about the given game; was it removed before you were able to '
                        'edit it?'),
                    ephemeral=True)
            case _:
                await super().on_error(error, interaction)


class SelectGameForMute(SelectGame):
    '''
    SelectGame drop-down for toggling notifications.
    '''

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback for a user selecting a game to toggle notifications for.
        '''
        with db_session():
            game = Game[self.game_id]
            game.muted = not game.muted
        await interaction.response.send_message(
            f'Muted {game.gamename}' if game.muted else f'Unmuted {game.gamename}')


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for the mute toggle.
        '''
        match error.__class__.__name__:
            case 'ObjectNotFound':
                await interaction.response.send_message(
                    ('Failed to toggle notifications for the given game; was it removed before you '
                        'selected it?'),
                    ephemeral=True)
                return
            case 'ValueAccessError' | 'IndexError':
                await interaction.response.send_message(GAME_SELECT_FAILED, ephemeral=True)
            case _:
                await super().on_error(error, interaction)


class SelectGameForDelete(SelectGame):
    '''
    SelectGame drop-down for deleting games.
    '''

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback for selecting a game to delete.
        '''
        await interaction.response.send_modal(GameDeleteModal(
            self.game_id,
            self.channel_id,
            self.bot))


class SelectGameForPing(SelectGame):
    '''
    SelectGame drop-down to initiate a manual ping.
    '''

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Game ping callback.
        '''
        with db_session():
            game = Game[self.game_id]
            logging.info(
                'User %s requested re-pinging for game %s (channel ID: %d)',
                get_discriminated_name(interaction.user),
                game.gamename,
                self.channel_id)
            await interaction.response.send_message(
                notify_messaging.get_content(game.lastup),
                embed=notify_messaging.get_embed(game),
                view=notify_messaging.get_view(game),
                ephemeral=True)
            game.lastnotified = time()


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for manually pinging a game.
        '''
        match error.__class__.__name__:
            case 'ObjectNotFound':
                await interaction.response.send_message(
                    ('Failed to re-ping the given game; was it removed before you were able to '
                        'send the notification?'),
                    ephemeral=True)
            case 'ValueAccessError' | 'IndexError':
                await interaction.response.send_message(GAME_SELECT_FAILED, ephemeral=True)
            case _:
                await super().on_error(error, interaction)


class GameModal(ChannelAwareModal):
    '''
    Base game modal that accepts a game_id.
    '''

    def __init__(self, game_id: int, *args, **kwargs):
        '''
        Constructor; sets the game_id.
        '''
        self._game_id = game_id
        super().__init__(*args, **kwargs)


    @property
    def game_id(self):
        '''
        Getter for game_id.
        '''
        return self._game_id


class GameEditModal(GameModal):
    '''
    Modal for editing a game.
    '''

    async def callback(self, interaction: Interaction):
        '''
        Submission handler for the edit game button.
        '''

        with db_session():
            game = Game[self.game_id]
            game.notifyinterval = self.get_child_value('notify_interval')
            game.minturns = self.get_child_value('min_turns')
        logging.info(
            'Updated information for %s (notifyinterval: %d, minturns: %d)',
            game.gamename,
            game.notifyinterval,
            game.minturns)
        await interaction.response.send_message(
            (f'Updated the configuration for {game.gamename} - set the re-ping interval to '
                f'{expand_seconds_to_string(game.notifyinterval)} and the minimum turns before '
                f'pinging to {game.minturns}.'),
            embed=game_messaging.get_game_edit_response_embed(game),
            ephemeral=True)


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for a failed game edit.
        '''
        match error.__class__.__name__:
            case 'ValueError':
                await interaction.response.edit_message(
                    content=("One of the fields had a value I wasn't expecting. Try again, and "
                        'make sure both fields contain a number.'))
            case 'ObjectNotFound':
                await interaction.response.send_message(
                    ('An error occurred; the game you were editing could no longer be found. Was '
                        'it removed?'),
                    ephemeral=True)
            case 'ValueAccessError' | 'IndexError':
                await interaction.response.send_message(GAME_SELECT_FAILED, ephemeral=True)
            case _:
                await super().on_error(error, interaction)


class GameDeleteModal(GameModal):
    '''
    Modal to confirm deletion of a game.
    '''

    async def callback(self, interaction: Interaction):
        with db_session():
            game = Game[self.game_id]
            game_name = game.gamename
            game.delete()
        logging.info('User %s has deleted game %s and all players attached to it',
            get_discriminated_name(interaction.user),
            game_name)
        await interaction.response.send_message(
            (f'Deleted all information about {game_name}; information about all unique players '
                'attached to this game has also been removed.'),
            ephemeral=True)


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for a failed game delete.
        '''
        match error.__class__.__name__:
            case 'ObjectNotFound':
                await interaction.response.send_message(
                    ('An error occurred; the game you were deleting could no longer be found. Was '
                        'it already removed?'),
                    ephemeral=True)
            case 'ValueAccessError' | 'IndexError':
                await interaction.response.send_message(GAME_SELECT_FAILED, ephemeral=True)
            case _:
                await super().on_error(error, interaction)
