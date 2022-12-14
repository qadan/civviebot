'''
CivvieBot cog to handle cleanup of stale games from the database.
'''

import logging
from datetime import datetime
from time import time
from pony.orm import db_session
from discord.ext import commands, tasks
from database.models import Game
from utils import config


class Cleanup(commands.Cog):
    '''
    Cleans up stale games from the database.
    '''

    def __init__(self, bot):
        '''
        Initialization; start the cleanup loop.
        '''
        self.bot: commands.Bot = bot
        self.cleanup.start() # pylint: disable=no-member


    @tasks.loop(seconds=config.get('cleanup_interval'))
    async def cleanup(self):
        '''
        Cleans up stale games from the database.

        A game is considered stale if the current time is greater than the sum of the game's last
        turn and the cleanup_limit set in configuration.
        '''
        now = time()
        cleanup_limit = config.get('cleanup_limit')
        with db_session():
            for game in Game.select(lambda g: g.lastturn + cleanup_limit < now):
                human_readable_last_turn = datetime.fromtimestamp(
                    game.lastturn).strftime('%m/%%d/%Y, %H:%M:%S')
                game.delete()
                logging.info(
                    'Deleted game %s (%d) and associated players during cleanup (last turn: %s)',
                    game.gamename,
                    game.id,
                    human_readable_last_turn
                )
                channel = await self.bot.fetch_channel(game.webhookurl.id)
                await channel.send((f'No activity detected in the game {game.gamename} for '
                    f'{cleanup_limit} seconds (last turn: {human_readable_last_turn}), so '
                    'information about the game and its associated players has been removed. If '
                    'you would like to continue recieving notifications for this game, a new turn '
                    'will have to be taken and CivvieBot will have to recieve a turn notification '
                    'for it'))


def setup(bot: commands.Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(Cleanup(bot))
