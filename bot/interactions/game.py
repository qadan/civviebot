'''
Interaction components to use with the 'game' cog.
'''

from datetime import datetime, timedelta
import logging
from traceback import format_list, extract_tb
from discord import Interaction, Embed
from discord.ui import Button
from discord.ext.commands import Bot
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from bot.cogs.cleanup import Cleanup
from bot.interactions.common import ChannelAwareModal, GameAwareButton, View
from bot.messaging import game as game_messaging
from database.connect import get_session
from database.models import Game, WebhookURL
from database.utils import delete_game
from utils.errors import base_error, handle_callback_errors
from utils.string import get_display_name, expand_seconds


logger = logging.getLogger(f'civviebot.{__name__}')


class ConfirmDeleteButton(GameAwareButton):
    '''
    Button that a user can click on to confirm deletion of a game.
    '''

    def __init__(self, game: int, *args, **kwargs):
        '''
        Constructor; set the label.
        '''
        kwargs['label'] = 'Delete game'
        super().__init__(game, *args, **kwargs)

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback; handles the actual deletion.
        '''
        delete_game(self.game)
        await interaction.response.send_message(
            content=(
                f'I am no longer tracking **{self.game}**. Any turn '
                'notifications for this game have also been removed. '
            ),
            embed=None,
            view=None
        )

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handling for the delete button.
        '''
        if isinstance(error, NoResultFound):
            await interaction.response.edit_message(
                content=(
                    'It seems like the game you were going to delete can no '
                    'longer be found. Was it already deleted?'
                )
            )
            return
        logger.error(
            'Unexpected failure in ConfirmDeleteButton: %s: %s\n%s',
            error.__class__.__name__,
            error,
            ''.join(format_list(extract_tb(error.__traceback__)))
        )
        await interaction.response.edit_message(
            content=(
                'An unknown error occurred; contact an administrator if this '
                'persists.'
            )
        )


class GameEditModal(ChannelAwareModal):
    '''
    Modal for editing a game.
    '''

    def __init__(self, game: int, *args, **kwargs):
        '''
        Constructor; sets the game_id.
        '''
        self._game = game
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: Interaction):
        '''
        Submission handler for the edit game button.
        '''
        response_embed = Embed()
        with get_session() as session:
            game = session.scalar(
                select(Game)
                .join(Game.webhookurl)
                .where(WebhookURL.channelid == interaction.channel_id)
                .where(Game.id == self.game)
            )
            game.remindinterval = int(self.get_child_value('notify_interval'))
            game.nextremind = (
                datetime.now() + timedelta(seconds=game.remindinterval)
                if game.remindinterval
                else None
            )
            game.minturns = int(self.get_child_value('min_turns'))
            session.commit()
            if game.remindinterval:
                response_embed.add_field(
                    name='Re-pings turns every:',
                    value=expand_seconds(game.remindinterval)
                )
            response_embed.add_field(
                name='Pings after turn:',
                value=game.minturns
            )
            logger.info(
                (
                    'User %s updated information for %s (notifyinterval: %d, '
                    'minturns: %d)'
                ),
                get_display_name(interaction.user),
                game.name,
                game.remindinterval,
                game.minturns
            )
            await interaction.response.send_message(
                content=f'Updated the configuration for {game.name}',
                embed=response_embed,
                view=None,
                ephemeral=True
            )

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for a failed game edit.
        '''
        if isinstance(error, ValueError):
            await interaction.response.edit_message(
                content=(
                    "One of the fields had a value I wasn't expecting. Try "
                    'again, and make sure both fields contain a number.'
                )
            )
            return
        await super().on_error(error, interaction)

    @property
    def game(self) -> id:
        '''
        The ID of the game being edited by this modal.
        '''
        return self._game


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
            content=(
                "I've successfully completed a round of cleanup.\n\n"
                + game_messaging.CLEANUP_CONTENT
            ),
            embed=game_messaging.get_cleanup_embed(interaction.channel_id),
            view=View(self)
        )

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Base on_error implementation.
        '''
        await base_error(logger, error, interaction=interaction)

    @property
    def bot(self) -> Bot:
        '''
        The bot that provided this button.
        '''
        return self._bot


class MergeGamesButton(Button):
    '''
    Confirmation button to merge two games together.
    '''

    def __init__(
        self,
        merge_source: Game,
        merge_target: Game,
        bot: Bot,
        *args,
        **kwargs
    ):
        '''
        Constructor; stash the merge target as well.
        '''
        self._merge_source = merge_source
        self._merge_target = merge_target
        self._bot = bot
        super().__init__(*args, **kwargs)

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback; merge self.game with self.merge_target.
        '''
        with get_session() as session:
            session.add(self.merge_target)
            self.merge_source.slug = self.merge_target.slug
            session.merge(self.merge_source)
            session.delete(self.merge_source)
            session.commit()
            interaction.response.edit_message(
                content=(
                    f'{self.merge_source.name} and existing data in this '
                    'channel has been merged with the existing game in '
                    f'{self.merge_target.webhookurl.channelid}.'
                ),
                embed=await game_messaging.get_info_embed(
                    self.merge_target,
                    self.bot
                ),
                view=None
            )

    @property
    def merge_target(self) -> Game:
        '''
        The destination game to send data from self.merge_source to.
        '''
        return self._merge_target

    @property
    def merge_source(self) -> Game:
        '''
        The game that is being merged with self.merge_target.
        '''
        return self._merge_source

    @property
    def bot(self) -> Bot:
        '''
        Stashed copy of the bot.
        '''
        return self._bot
