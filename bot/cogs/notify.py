'''
CivvieBot cog that sends out turn notifications.
'''

import logging
from time import time
from discord.ext import tasks, commands
from pony.orm import db_session
from database import models
from utils import config
import bot.messaging.notify as notify_messaging

logger = logging.getLogger(f'civviebot.{__name__}')

class Notify(commands.Cog):
    '''
    Cog to send out turn notifications.
    '''

    def __init__(self, bot):
        '''
        Initialization; starts the notification loop.
        '''
        self.bot: commands.Bot = bot
        self.notify.start() # pylint: disable=no-member


    @tasks.loop(seconds=config.get('notification_interval'))
    async def notify(self):
        '''
        Sends out two types of turn notifications for games that are not 'muted' and whose current
        turn is above their configured 'minturns':

        First, notifications are sent out for games that assert that their last notification was
        less recent than the current turn notification from Civilization 6.

        Second, notifications are re-sent for games that assert that their stale notification
        interval has passed since the last ping.

        Either way, 'lastnotified' is updated to the current time.
        '''
        limit = config.get('limit')
        now = time()
        with db_session():
            # Round of standard notifications.
            for game in models.Game.select(lambda g:
                g.lastnotified < g.lastturn
                and g.muted is False
                and g.turn > g.minturns).order_by(lambda g: g.lastturn)[:limit]:
                await self.send_notification(game)
                logger.info(('Standard turn notification sent for %s (turn %d, last notified: '
                    '%d, last turn: %d)'),
                    game.gamename,
                    game.turn,
                    game.lastnotified,
                    game.lastturn)
                game.lastnotified = now
            # Round of long downtime notifications.
            for game in models.Game.select(lambda g:
                g.muted is False
                and g.turn > g.minturns
                and g.notifyinterval is not None
                and g.lastnotified + g.notifyinterval < now
            ).order_by(lambda g: g.lastnotified)[:limit]:
                await self.send_notification(game)
                logger.info(('Re-ping sent for %s (turn %d, last notified: '
                    '%d, last turn: %d, notify interval: %d)'),
                    game.gamename,
                    game.turn,
                    game.lastnotified,
                    game.lastturn,
                    game.notifyinterval)
                game.lastnotified = now


    async def send_notification(self, game: models.Game):
        '''
        Sends a notification for the current turn in the given game.

        Requires database context, as this updates the lastnotify for the given game.
        '''
        channel = await self.bot.fetch_channel(game.webhookurl.channelid)
        await channel.send(
            content=notify_messaging.get_content(game.lastup),
            embed=notify_messaging.get_embed(game),
            view=notify_messaging.get_view(game))


def setup(bot: commands.Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(Notify(bot))
