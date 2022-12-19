'''
CivvieBot cog to handle cleanup of stale games from the database.
'''

import logging
from datetime import datetime
from time import time
from pony.orm import db_session
from discord.ext import commands, tasks
from database.models import Game, Player, WebhookURL
from utils import config
from utils.utils import expand_seconds_to_string


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
        self.cleanup.start() # pylint: disable=no-member


    @tasks.loop(seconds=config.get('cleanup_interval'))
    async def cleanup(self):
        '''
        Cleans up stale games, delete-flagged URLs, and delete-flagged players.
        '''
        cleanup_limit = config.get('cleanup_limit')
        await self.remove_stale_games(cleanup_limit)
        Player.select(cleanup=True)[:cleanup_limit].delete(bulk=True)
        WebhookURL.select(cleanup=True)[:cleanup_limit].delete(bulk=True)


    async def remove_stale_games(self, limit: int):
        '''
        Removes up to limit stale games from the database.

        A game is considered stale if the current time is greater than the sum of the game's last
        turn and the stale_game_length set in configuration.
        '''
        now = time()
        stale_len = config.get('stale_game_length')
        with db_session():
            for game in Game.select(lambda g: g.lastturn + stale_len < now)[:limit]:
                last_turn = datetime.fromtimestamp(
                    game.lastturn).strftime('%m/%%d/%Y, %H:%M:%S')
                game.delete()
                logging.info(
                    'Deleted game %s (%d) and associated players during cleanup (last turn: %s)',
                    game.gamename,
                    game.id,
                    last_turn)
                channel = await self.bot.fetch_channel(game.webhookurl.id)
                await channel.send((f'No activity detected in the game {game.gamename} for '
                    f'{expand_seconds_to_string(stale_len)} (last turn: {last_turn}), so'
                    'information about the game has been removed. If you would like to continue '
                    'recieving notifications for this game, a new turn will have to be taken and '
                    'CivvieBot will have to recieve a turn notification for it'))


def setup(bot: commands.Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(Cleanup(bot))
