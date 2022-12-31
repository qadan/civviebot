'''
CivvieBot cog that sends out turn notifications.
'''

import logging
from time import time
from discord.ext import tasks, commands
from pony.orm import db_session
from database import models
import bot.messaging.notify as notify_messaging
from utils import config, utils

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
        self.notify_duplicates.start() # pylint: disable=no-member

    @tasks.loop(seconds=config.get('notification_interval'))
    async def notify_turns(self):
        '''
        Sends out two types of turn notifications for games that are not 'muted':

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
                and g.turn > g.minturns
                and g.lastup.id not in g.pinged).order_by(lambda g: g.lastturn)[:limit]:
                await self.send_notification(game)
                game.lastnotified = now
                game.pinged.append(game.lastup.id)
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
                game.lastnotified = now
                logger.info(('Re-ping sent for %s (turn %d, last notified: '
                    '%d, last turn: %d, notify interval: %d)'),
                    game.gamename,
                    game.turn,
                    game.lastnotified,
                    game.lastturn,
                    game.notifyinterval)

    async def send_notification(self, game: models.Game):
        '''
        Sends a notification for the current turn in the given game.

        Requires database context, as this updates the lastnotify for the given game.
        '''
        channel = await self.bot.fetch_channel(game.webhookurl.channelid)
        await channel.send(
            content=notify_messaging.get_content(game),
            embed=notify_messaging.get_embed(game),
            view=notify_messaging.get_view(game))

    @tasks.loop(seconds=config.get('notification_interval'))
    async def notify_duplicates(self):
        '''
        Sends a round of duplicate game notifications.
        '''
        limit = config.get('limit')
        with db_session():
            for game in models.Game.select(lambda g: g.warnedduplicate is False)[:limit]:
                logger.info('Sending duplicate notification for %s', game.gamename)
                channel = await self.bot.fetch_channel(game.webhookurl.channelid)
                if channel:
                    await channel.send(('**NOTICE**: I got a notification about a game in this '
                        f'channel called **{game.gamename}** (at the webhook URL '
                        f'{utils.generate_url(game.webhookurl.slug)}) that appears to be a '
                        'duplicate, since its current turn is lower than the one I was already '
                        "tracking. If you want to start a new game with the same name using this "
                        "same URL, and you don't want to wait for the existing one to get "
                        f"automatically cleaned up, you'll need tomanually remove it first using "
                        '`/{game_name}_manage delete`.'))
                else:
                    logger.error(('Tried to send a duplicate warning to %s for game %s, but the '
                        'channel could not be found'),
                        game.webhookurl.channelid,
                        game.gamename)
                game.warnedduplicate = True

def setup(bot: commands.Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(Notify(bot))
