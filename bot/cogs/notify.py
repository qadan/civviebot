'''
CivvieBot cog that sends out turn notifications.
'''

import logging
from time import time
from discord.ext import tasks, commands
from pony.orm import db_session
from database import models
from utils import config
from bot.cogs.game import NAME as game_name
import bot.messaging.notify as notify_messaging
from utils.utils import generate_url

logger = logging.getLogger(f'civviebot.{__name__}')

class Notify(commands.Cog):
    '''
    Cog to send out notifications.
    '''

    def __init__(self, bot):
        '''
        Initialization; starts the notification loop.
        '''
        self.bot: commands.Bot = bot
        self.notify_turns.start() # pylint: disable=no-member
        self.warn_limits.start() # pylint: disable=no-member


    @tasks.loop(seconds=config.get('notification_interval'))
    async def notify_turns(self):
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
                if game.webhookurl.warnlimit == False:
                    game.webhookurl.warnlimit = True
                    await self.send_notification(game, warn_limit=True)
                else:
                    await self.send_notification(game)
                game.lastnotified = now
                logger.info(('Standard turn notification sent for %s (turn %d, last notified: '
                    '%d, last turn: %d)'),
                    game.gamename,
                    game.turn,
                    game.lastnotified,
                    game.lastturn)
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


    @tasks.loop(seconds=config.get('notification_interval'))
    async def warn_limits(self):
        '''
        Sends notifications for URLs approaching their limit.
        '''
        limit = config.get('limit')
        with db_session():
            for url in models.WebhookURL.select(
                lambda u: u.warnlimit == False and len(u.games) == 25)[:limit]:
                url.warnlimit = True
                channel = await self.bot.fetch_channel(url.channelid)
                await channel.send(
                    content=("**NOTICE**: I'm now tracking 25 games using the webhook URL "
                        f"{generate_url(url.slug)}. I'll have to ignore any new games using it "
                        'until one or more of those games is removed from tracking. You can either '
                        "wait for them to automatically get cleaned up after they've been stale "
                        'for a while, or you can clean some of them up manually using '
                        f'`/{game_name}_manage delete`.'))


    async def send_notification(self, game: models.Game, warn_limit: bool = False):
        '''
        Sends a notification for the current turn in the given game.

        Requires database context, as this updates the lastnotify for the given game.
        '''
        channel = await self.bot.fetch_channel(game.webhookurl.channelid)
        await channel.send(
            content=notify_messaging.get_content(game, warn_limit=warn_limit),
            embed=notify_messaging.get_embed(game),
            view=notify_messaging.get_view(game))


def setup(bot: commands.Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(Notify(bot))
