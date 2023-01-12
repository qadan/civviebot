'''
CivvieBot cog that sends out turn notifications.
'''

import logging
from datetime import datetime, timedelta
from discord.ext import tasks, commands
from sqlalchemy import select
from database.models import TurnNotification, Game
from database.utils import get_session
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
        with get_session() as session:
            # Round of standard notifications.
            standard_games = (select(TurnNotification)
                .join(TurnNotification.game)
                .where(TurnNotification.lastnotified == None)
                .where(Game.muted == False)
                .where(TurnNotification.turn > Game.minturns))
            standard_games = standard_games.limit(config.NOTIFY_LIMIT)
            print(session.scalars(standard_games).all())
            for notification in session.scalars(standard_games).all():
                await self.send_notification(notification)
                logger.info(('Standard turn notification sent for %s (turn %d, last outgoing '
                    'notification: %s, last incoming notification: %s)'),
                    notification.game.name,
                    notification.turn,
                    (notification.lastnotified.strftime('%m/%%d/%Y, %H:%M:%S')
                        if notification.lastnotified
                        else 'no previous notification'),
                    notification.logtime.strftime('%m/%%d/%Y, %H:%M:%S'))
                notification.lastnotified = now
                notification.game.nextremind = now + timedelta(0, notification.game.remindinterval)
            # Round of reminder notifications.
            reminders = (select(TurnNotification)
                .join(TurnNotification.game)
                .where(Game.nextremind != None)
                .where(Game.nextremind > now)
                .where(Game.muted == False)
                .where(TurnNotification.turn > Game.minturns))
            reminders = reminders.limit(config.NOTIFY_LIMIT).order_by(TurnNotification.lastnotified)
            for notification in session.scalars(reminders).all():
                await self.send_notification(notification)
                notification.lastnotified = now
                notification.game.nextremind = now + timedelta(0, notification.game.remindinterval)
                logger.info(('Re-ping sent for %s (turn %d, last outgoing notification: %s, last '
                    'incominf notification: %s, reminder interval: %d seconds)'),
                    notification.game.name,
                    notification.turn,
                    notification.lastnotified.strftime('%m/%%d/%Y, %H:%M:%S'),
                    notification.logtime.strftime('%m/%%d/%Y, %H:%M:%S'),
                    notification.game.remindinterval)
            session.commit()

    async def send_notification(self, notification: TurnNotification):
        '''
        Sends a notification for the current turn in the given game.
        '''
        channel = await self.bot.fetch_channel(notification.game.webhookurl.channelid)
        await channel.send(
            content=notify_messaging.get_content(notification),
            embed=notify_messaging.get_embed(notification),
            view=notify_messaging.get_view(notification))

    @tasks.loop(seconds=config.NOTIFY_INTERVAL)
    async def notify_duplicates(self):
        '''
        Sends a round of duplicate game notifications.
        '''
        with get_session() as session:
            for game in session.scalars(select(Game)
                .where(Game.duplicatewarned == False)
                .limit(config.NOTIFY_LIMIT)).all():
                channel = await self.bot.fetch_channel(game.webhookurl.channelid)
                if channel:
                    await channel.send(('**NOTICE**: I got a notification about a game in this '
                        f'channel called **{game.name}** (at the webhook URL '
                        f'{utils.generate_url(game.slug)}) that appears to be a '
                        'duplicate, since its current turn is lower than the one I was already '
                        "tracking. If you want to start a new game with the same name using this "
                        "same URL, and you don't want to wait for the existing one to get "
                        "automatically cleaned up, you'll need to manually remove it first."))
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
