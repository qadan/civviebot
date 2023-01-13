'''
Interaction components to use with the 'game' cog.
'''

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
from database.models import Game, WebhookURL
from database.utils import delete_game, get_session
from utils.errors import base_error
from utils.utils import get_discriminated_name, expand_seconds_to_string, handle_callback_errors

logger = logging.getLogger(f'civviebot.{__name__}')

class ConfirmDeleteButton(GameAwareButton):
    '''
    Button that a user can click on to confirm deletion of a game.
    '''

    def __init__(self, game: str, *args, **kwargs):
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
        delete_game(self.game, interaction.channel_id)
        await interaction.response.send_message(
            content=(f'The game **{self.game}** and any attached players that are not part of '
                'other active games have been deleted.'),
            embed=None,
            view=None)

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handling for the delete button.
        '''
        if isinstance(error, NoResultFound):
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

class GameEditModal(ChannelAwareModal):
    '''
    Modal for editing a game.
    '''

    def __init__(self, game: str, *args, **kwargs):
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
            game = session.scalar(select(Game)
                .join(Game.webhookurl)
                .where(WebhookURL.channelid == interaction.channel_id)
                .where(Game.name == self.game))
            game.remindinterval = self.get_child_value('notify_interval')
            game.minturns = self.get_child_value('min_turns')
            session.commit()
            if game.remindinterval:
                response_embed.add_field(
                    name='Re-pings turns every:',
                    value=expand_seconds_to_string(game.remindinterval))
            response_embed.add_field(
                name='Pings after turn:',
                value=game.minturns)
            logger.info(
                'User %s updated information for %s (notifyinterval: %d, minturns: %d)',
                get_discriminated_name(interaction.user),
                game.name,
                game.remindinterval,
                game.minturns)
            await interaction.response.send_message(
                content=f'Updated the configuration for {game.name}',
                embed=response_embed,
                view=None,
                ephemeral=True)

    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for a failed game edit.
        '''
        if isinstance(error, ValueError):
            await interaction.response.edit_message(
                content=("One of the fields had a value I wasn't expecting. Try again, and make "
                    'sure both fields contain a number.'))
            return
        await super().on_error(error, interaction)

    @property
    def game(self) -> str:
        '''
        Getter for the associated game.
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
            content="I've successfully completed a round of cleanup.\n\n"
                + game_messaging.CLEANUP_CONTENT,
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
