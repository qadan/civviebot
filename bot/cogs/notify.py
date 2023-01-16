'''
CivvieBot cog that sends out turn notifications.
'''

import logging
from datetime import datetime, timedelta
from typing import Tuple
from discord.ext import tasks, commands
from sqlalchemy import select, Row, Subquery, Select
from database.connect import get_session
from database.models import TurnNotification, Game, WebhookURL
from database.utils import date_rank_subquery
import bot.messaging.notify as notify_messaging
from utils import config

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

    @staticmethod
    def notification_query(
        subquery: Subquery) -> Select[Tuple[int, str, str, str, datetime, datetime, int, int]]:
        '''
        Gets the base query to use for notifications.

        Gives the tuple back in model defined order, plus the WebhookURL.channelid.
        '''
        return (select(
            subquery.c.turn,
            subquery.c.playername,
            subquery.c.gamename,
            subquery.c.slug,
            subquery.c.logtime,
            subquery.c.lastnotified,
            subquery.c.date_rank,
            WebhookURL.channelid)
        .join(Game, Game.name == subquery.c.gamename)
        .join(WebhookURL, WebhookURL.slug == subquery.c.slug)
        .where(Game.muted == False) # pylint: disable=singleton-comparison
        .where(subquery.c.turn > Game.minturns)
        .where(subquery.c.date_rank == 1))

    @tasks.loop(seconds=config.NOTIFY_INTERVAL)
    async def notify_turns(self):
        '''
        Sends out two types of turn notifications for games that are not 'muted':

        First, notifications are sent out for games that assert that their last notification was
        less recent than the current turn notification from Civilization 6.

        Second, notifications are re-sent for games that assert that their stale notification
        interval has passed since the last ping.

        Either way, 'lastnotified' is updated to the current time.
        '''
        now = datetime.now()
        subquery = date_rank_subquery()

        # Round of standard notifications.
        with get_session() as session:
            notifications = session.execute(self.notification_query()
                .where(subquery.c.lastnotified == None) # pylint: disable=singleton-comparison
                .limit(config.NOTIFY_LIMIT))
        for notification in notifications:
            await self.send_notification(self.bot, notification)
            logger.info(('Standard turn notification sent for %s (turn %d, last outgoing '
                'notification: %s, last incoming notification: %s)'),
                notification.gamename,
                notification.turn,
                (notification.lastnotified.strftime('%m/%%d/%Y, %H:%M:%S')
                    if notification.lastnotified
                    else 'no previous notification'),
                notification.logtime.strftime('%m/%%d/%Y, %H:%M:%S'))

        # Round of reminder notifications.
        with get_session() as session:
            notifications = session.execute(self.notification_query(subquery)
                .where(Game.nextremind != None) # pylint: disable=singleton-comparison
                .where(Game.nextremind < now)
                .limit(config.NOTIFY_LIMIT))
        for notification in notifications:
            await self.send_notification(self.bot, notification)
            logger.info(('Re-ping sent for %s (turn %d, last outgoing notification: %s, last '
                'incoming notification: %s)'),
                notification.gamename,
                notification.turn,
                notification.lastnotified.strftime('%m/%%d/%Y, %H:%M:%S'),
                notification.logtime.strftime('%m/%%d/%Y, %H:%M:%S'))

    @staticmethod
    async def send_notification(bot: commands.Bot, notification: Row[Tuple]):
        '''
        Sends a notification for the current turn in the given game.

        The input Row[Tuple] expects all fields from TurnNotification, plus the channelid from its
        linked WebhookURL.
        '''
        channel = await bot.fetch_channel(notification.channelid)
        # Directly load the object and update.
        now = datetime.now()
        with get_session() as session:
            to_modify = session.scalar(select(TurnNotification)
                .where(TurnNotification.turn == notification.turn)
                .where(TurnNotification.slug == notification.slug)
                .where(TurnNotification.playername == notification.playername)
                .where(TurnNotification.gamename == notification.gamename))
            await channel.send(
                content=notify_messaging.get_content(to_modify),
                embed=notify_messaging.get_embed(to_modify),
                view=notify_messaging.get_view(to_modify))
            to_modify.lastnotified = now
            print(to_modify.game.nextremind)
            to_modify.game.nextremind = (now
                + timedelta(seconds=to_modify.game.remindinterval))
            print(to_modify.game.nextremind)
            session.commit()

    @tasks.loop(seconds=config.NOTIFY_INTERVAL)
    async def notify_duplicates(self):
        '''
        Sends a round of duplicate game notifications.
        '''
        with get_session() as session:
            for game in session.scalars(select(Game)
                .where(Game.duplicatewarned == False) # pylint: disable=singleton-comparison
                .limit(config.NOTIFY_LIMIT)):
                channel = await self.bot.fetch_channel(game.webhookurl.channelid)
                if channel:
                    await channel.send(('**NOTICE**: I got a notification about a game in this '
                        f'channel called **{game.name}** (at the webhook URL '
                        f'{game.full_url}) that appears to be a duplicate, since its current turn '
                        'is lower than the one I was already tracking. If you want to start a new '
                        "new game with the same name using this same URL, and you don't want to "
                        "wait for the existing one to get automatically cleaned up, you'll need to "
                        "manually remove it first."))
                else:
                    logger.error(('Tried to send a duplicate warning to %s for game %s, but the '
                        'channel could not be found'),
                        game.webhookurl.channelid,
                        game.name)
                game.duplicatewarned = True
            session.commit()

def setup(bot: commands.Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(Notify(bot))
