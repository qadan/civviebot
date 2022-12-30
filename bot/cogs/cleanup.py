'''
CivvieBot cog to handle cleanup of stale games from the database.
'''

import logging
from datetime import datetime
from time import time
from pony.orm import db_session, left_join
from discord.ext import commands, tasks
from database.models import Player, Game, WebhookURL
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


    @tasks.loop(seconds=config.get('cleanup_interval'))
    async def run_cleanup(self):
        '''
        Cleans up stale games, delete-flagged URLs, and delete-flagged players.
        '''
        await self.cleanup(self.bot)
    

    @staticmethod
    async def cleanup(bot: commands.Bot, limit_channel: int = None):
        '''
        Cleans up games, players, and webhook URLs.
        '''
        now = time()
        limit = config.get('cleanup_limit')
        stale_len = config.get('stale_game_length')
        # Cheaper than hanging onto a ton of entities.
        games_removed = 0
        players_removed = 0
        urls_removed = 0
        with db_session():
            games = (Game.select(lambda g: g.lastturn + stale_len < now 
                and g.webhookurl.channelid == limit_channel)[:limit]
                if limit_channel else
                Game.select(lambda g: g.lastturn + stale_len < now)[:limit])
            for game in games:
                last_turn = datetime.fromtimestamp(
                    game.lastturn).strftime('%m/%%d/%Y, %H:%M:%S')
                game.delete()
                games_removed += 1
                logger.info(
                    'Deleted game %s (%d) and associated players during cleanup (last turn: %s)',
                    game.gamename,
                    game.id,
                    last_turn)
                channel = await bot.fetch_channel(game.webhookurl.id)
                await channel.send((f'No activity detected in the game {game.gamename} for '
                    f'{expand_seconds_to_string(stale_len)} (last turn: {last_turn}), so'
                    'information about the game has been removed. If you would like to continue '
                    'recieving notifications for this game, a new turn will have to be taken and '
                    'CivvieBot will have to recieve a turn notification for it'))
        # Pony appears to have inaccurate documentation regarding bulk delete;
        # we should be able to attach .delete(bulk=True) to the end of the
        # select, but db.EntityMeta.select() doesn't return the type of object
        # the documentation claims it should. I may file a bug report about this
        # but the lack of activity on Pony itself over the last year is a little
        # troubling. If it continues, a rework using a non-ORM query builder
        # like PyPika may be worth considering.
        with db_session():
            for player in (left_join(p for p in Player for g in p.games 
                if p.cleanup == True
                and g.webhookurl.channelid == limit_channel)[:limit]
                if limit_channel else Player.select(lambda p: p.cleanup == True)[:limit]):
                player.delete()
                players_removed += 1
            if not limit_channel:
                for url in WebhookURL.select(lambda w: w.cleanup == True)[:limit]:
                    url.delete()
                    urls_removed += 1

        logger.info('Round of cleanup has finished; removed %d games, %d players, %d URLs',
            games_removed,
            players_removed,
            urls_removed)


def setup(bot: commands.Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(Cleanup(bot))
