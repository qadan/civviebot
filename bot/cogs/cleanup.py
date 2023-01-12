'''
CivvieBot cog to handle cleanup of stale games from the database.
'''

import logging
from time import time
from sqlalchemy import select
from discord.ext import commands, tasks
from database.models import Game
from database.utils import get_session
from utils import config
from utils.utils import expand_seconds_to_string

logger = logging.getLogger(f'civviebot.{__name__}')

class Cleanup(commands.Cog):
    '''
    Cleans up stale games from the database.
    '''

    def __init__(self, bot):
        '''
        Initialization; start the cleanup loop.
        '''
        self.bot: commands.Bot = bot
        # Apparently this isn't wrapped.
        self.run_cleanup.start() # pylint: disable=no-member

    @tasks.loop(seconds=config.CLEANUP_INTERVAL)
    async def run_cleanup(self):
        '''
        Cleans up stale games, delete-flagged URLs, and delete-flagged players.
        '''
        await self.cleanup(self.bot)

    @staticmethod
    async def cleanup(bot: commands.Bot, limit_channel: int = None):
        '''
        Cleans up games over the stale game length.
        '''
        now = time()
        # Going to just increment this instead of hanging onto rows.
        removed = 0
        with get_session() as session:
            query = (select(Game).where(
                Game.turns[0].logtime.total_seconds() + config.STALE_GAME_LENGTH < now)
                .limit(config.CLEANUP_LIMIT))
            if limit_channel:
                query = query.where(Game.webhookurl.channelid == limit_channel)
            for game in session.scalars(query).all():
                last_turn = game.turns[0].logtime.strftime('%m/%%d/%Y, %H:%M:%S')
                session.delete(game)
                removed += 1
                logger.info(
                    'Deleted game %s (channel: %d) during cleanup (last turn: %s)',
                    game.name,
                    game.webhookurl.channelid,
                    last_turn)
                channel = await bot.fetch_channel(game.webhookurl.id)
                await channel.send((f'No activity detected in the game {game.name} for '
                    f'{expand_seconds_to_string(config.STALE_GAME_LENGTH)} (last turn: '
                    f'<t:{int(game.turns[0].logtime)}:R>), so tracking information about the game '
                    'has been automatically cleaned up. If you would like to continue recieving '
                    'notifications for this game, a new turn will have to be taken and CivvieBot '
                    'will have to recieve a turn notification for it.'))
        logger.info('Round of cleanup has finished; removed %d games', removed)

def setup(bot: commands.Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(Cleanup(bot))
