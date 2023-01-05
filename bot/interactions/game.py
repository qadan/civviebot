'''
Interaction components to use with the 'game' cog.
'''

import logging
from time import time
from traceback import format_list, extract_tb
from discord import SelectOption, Interaction, Embed, EmbedField
from discord.ui import Button
from discord.ext.commands import Bot
from pony.orm import db_session, ObjectNotFound
from bot.cogs.cleanup import Cleanup
from bot.cogs.player import NAME as PLAYER_NAME
from bot.messaging import notify as notify_messaging
from bot.interactions.common import (MinTurnsInput,
    NotifyIntervalInput,
    ChannelAwareModal,
    GameAwareButton,
    View,
    SelectGame)
from bot.messaging import game as game_messaging
from database.models import Game, Player
from utils import config
from utils.errors import base_error
from utils.utils import (
    generate_url,
    get_discriminated_name,
    expand_seconds_to_string,
    handle_callback_errors)

logger = logging.getLogger(f'civviebot.{__name__}')

class SelectGameForInfo(SelectGame):
    '''
    SelectGame drop-down for getting info about a game.
    '''

    @staticmethod
    def get_info_embed(game_id: int):
        '''
        Gets the embed to provide info about a game.
        '''
        with db_session():
            game = Game[game_id]
            if not game:
                embed = Embed(title='Missing game')
                embed.description=('Failed to find the given game; was it deleted before '
                    'information could be provided?')
            embed = Embed(title=game.gamename)
            embed.add_field(name='Current turn:', value=game.turn, inline=True)
            embed.add_field(name='Current player:', value=game.lastup.playername, inline=True)
            embed.add_field(
                name='Most recent turn:',
                value=f'<t:{int(game.lastturn)}:R>',
                inline=True)
            if game.notifyinterval and game.turn > game.minturns:
                embed.add_field(
                    name='Next reminder:',
                    value=('<t:'
                        + str(int(game.notifyinterval + game.lastnotified))
                        + '>'),
                    inline=True)
            embed.add_field(name='Notifies after:', value=f'Turn {game.minturns}', inline=True)
            embed.add_field(name='Is muted:', value='Yes' if game.muted else 'No', inline=True)
            embed.add_field(name='Tracked players:', value=len(game.players), inline=True)
            embed.add_field(name='Webhook URL:', value=generate_url(game.webhookurl.slug))
        embed.set_footer(text=('If you\'re part of this game, place the above webhook URL in your '
            'Civilization 6 settings to send notifications to CivvieBot when you take your turn '
            f'(use "/{config.COMMAND_PREFIX} quickstart" for more setup information). For a list '
            f'of known players in this game, use "/{config.COMMAND_PREFIX}game players".'))
        return embed

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback for a user selecting a game from the drop-down to get info about.
        '''
        await interaction.response.edit_message(
            content=None,
            embed=self.get_info_embed(self.game_id))

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for getting information.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content=('Failed to get information about the given game; was it removed before '
                    'you were able to get information about it?'))
            return
        await super().on_error(error, interaction)

class SelectGameForPlayers(SelectGame):
    '''
    SelectGame drop-down to get a list of players.
    '''

    @staticmethod
    def player_to_field(player: Player, bot: Bot) -> EmbedField:
        '''
        Gets the EmbedField to use for a given player in the list.
        '''
        if player.discordid:
            user = bot.get_user(int(player.discordid))
            link = get_discriminated_name(user) if user else (f'MISSING (`/{PLAYER_NAME}_manage '
                'unlink` to remove)')
        else:
            link = 'No linked user'
        return EmbedField(name=player.playername, value=link, inline=True)

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        embed = Embed()
        with db_session():
            game = Game[self.game_id]
            embed.fields = [self.player_to_field(player, self.bot) for player in game.players]
        await interaction.response.edit_message(
            content=None,
            embed=embed)

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for missing games.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content=('Failed to find the selected game; was it removed before you could get '
                    'the player list?'),
                embed=None)
            return
        await super().on_error(error, interaction)

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
        notify_interval = game.notifyinterval if game.notifyinterval else 0
        await interaction.response.send_modal(GameEditModal(
            self.game_id,
            self.channel_id,
            self.bot,
            NotifyIntervalInput(notify_interval=notify_interval),
            MinTurnsInput(min_turns=game.minturns),
            title=f'Editing information about {game.gamename}'))

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for editing a game.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content=('Failed to edit about the given game; was it removed before you were able '
                    'to edit it?'))
            return
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
        await interaction.response.edit_message(
            content=(f'Notifications for the game **{game.gamename}** are now muted.' if game.muted
                else f'Notifications for the game **{game.gamename}** are now unmuted.'),
            view=None)

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for the mute toggle.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content=('Failed to toggle notifications for the given game; was it removed before '
                    'you selected it?'))
            return
        await super().on_error(error, interaction)

    def get_game_as_option(self, game: Game) -> SelectOption:
        '''
        Transforms a Game object into a SelectOption; adds an emoji for its current muted status.
        '''
        option = super().get_game_as_option(game)
        option.emoji = '🔇' if game.muted else '🔊'
        return option

class SelectGameForDelete(SelectGame):
    '''
    SelectGame drop-down for deleting games.
    '''

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback for selecting a game to delete.
        '''
        with db_session():
            game = Game[self.game_id]
        await interaction.response.edit_message(
            content=(f'Are you sure you want to delete **{game.gamename}**? This will remove any '
                'attached players that are not currently part of any other game.'),
            embed=SelectGameForInfo.get_info_embed(self.game_id),
            view=View(ConfirmDeleteButton(self.game_id)))

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for the game delete selection.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content=('It seems like the game you selected can no longer be found. Was it '
                    'already deleted?'))
        await super().on_error(error, interaction)

class ConfirmDeleteButton(GameAwareButton):
    '''
    Button that a user can click on to confirm deletion of a game.
    '''

    def __init__(self, game_id: int, *args, **kwargs):
        '''
        Constructor; set the label.
        '''
        kwargs['label'] = 'Delete game'
        super().__init__(game_id, *args, **kwargs)

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback; handles the actual deletion.
        '''
        with db_session():
            game = Game[self.game_id]
            game_name = game.gamename
            game.webhookurl.warnedlimit = None
            game.delete()
        await interaction.response.edit_message(
            content=(f'The game **{game_name}** and any attached players that are not part of '
                'other active games have been deleted.'),
            embed=None,
            view=None)

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handling for the delete button.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content=('It seems like the game you were going to delete can no longer be found. '
                    'Was it already deleted?'))
            return
        logger.error(
            'Unexpected failure in ConfirmDeleteButton: %s: %s\n%s',
            error.__class__.__name__,
            error,
            ''.join(format_list(extract_tb(error.__traceback__))))
        await interaction.response.edit_message(
            content='An unknown error occurred; contact an administrator if this persists.')

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
            logger.info(
                'User %s requested re-pinging for game %s (channel ID: %d)',
                get_discriminated_name(interaction.user),
                game.gamename,
                self.channel_id)
            await interaction.response.send_message(
                content=notify_messaging.get_content(game),
                embed=notify_messaging.get_embed(game),
                view=notify_messaging.get_view(game))
            game.lastnotified = time()

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for manually pinging a game.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content=('Failed to re-ping the given game; was it removed before you were able to '
                    'send the notification?'))
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
        response_embed = Embed()
        with db_session():
            game = Game[self.game_id]
            game.notifyinterval = self.get_child_value('notify_interval')
            game.minturns = self.get_child_value('min_turns')
        if game.notifyinterval:
            response_embed.add_field(
                name='Re-pings turns after:',
                value=expand_seconds_to_string(game.notifyinterval))
        response_embed.add_field(
            name='Pings after turn:',
            value=game.minturns)
        logger.info(
            'User %s updated information for %s (notifyinterval: %d, minturns: %d)',
            get_discriminated_name(interaction.user),
            game.gamename,
            game.notifyinterval,
            game.minturns)
        await interaction.response.edit_message(
            content=f'Updated the configuration for {game.gamename}',
            embed=response_embed,
            view=None)

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for a failed game edit.
        '''
        if isinstance(error, ValueError):
            await interaction.response.edit_message(
                content=("One of the fields had a value I wasn't expecting. Try again, and make "
                    'sure both fields contain a number.'))
            return
        if isinstance(error, ObjectNotFound):
            await interaction.response.send_message(
                content=('An error occurred; the game you were editing could no longer be found. '
                    'Was it removed?'))
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
        logger.info('User %s has deleted game %s and all players attached to it',
            get_discriminated_name(interaction.user),
            game_name)
        await interaction.response.edit_message(
            content=(f'Deleted all information about {game_name}; information about all unique '
                'players attached to this game has also been removed.'))

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for a failed game delete.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content=('An error occurred; the game you were deleting could no longer be found. '
                    'Was it already removed?'))
            return
        await super().on_error(error, interaction)

class TriggerCleanupButton(Button):
    '''
    Button whose callback triggers a cleanup.
    '''

    def __init__(self, bot: Bot, *args, **kwargs):
        '''
        Constructor; sets the bot and label.
        '''
        self._bot = bot
        kwargs['label'] = 'Run cleanup now'
        super().__init__(*args, **kwargs)

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback; runs a round of cleanup.
        '''
        await Cleanup.cleanup(self.bot, limit_channel=interaction.channel_id)
        await interaction.response.edit_message(
            content="I've successfully completed a round of cleanup.\n\n" + game_messaging.CONTENT,
            embed=game_messaging.get_cleanup_embed(interaction.channel_id),
            view=View(self))

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Base on_error implementation.
        '''
        await base_error(logger, error, interaction)

    @property
    def bot(self) -> Bot:
        '''
        The bot that provided this button.
        '''
        return self._bot
