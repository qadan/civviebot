'''
Builders for portions of messages dealing with turn notification.
'''

import logging
from datetime import datetime, timedelta
from discord import Embed
from sqlalchemy.orm import Session
from database.models import TurnNotification
from database.utils import get_session
from utils.utils import generate_url
from bot.interactions.common import View
from bot.interactions.notify import MuteButton, PlayerLinkButton

logger = logging.getLogger(f'civviebot.{__name__}')

def get_content(notification: TurnNotification) -> str:
    '''
    Gets the content for a turn notification message.
    '''
    tag = (f'<@{notification.player.discordid}>'
        if notification.player.discordid
        else notification.player.name)
    return (f"It's {tag}'s turn!"
        if not notification.lastnotified
        else f"**Reminder**: it's {tag}'s turn (<t:{int(notification.logtime.timestamp())}:R>)")

def get_embed(notification: TurnNotification) -> Embed:
    '''
    Gets the embed for a turn notification message.
    '''
    embed = Embed(title=notification.game.name)
    embed.add_field(
        name='Current Player',
        value=notification.player.name,
        inline=True)
    embed.add_field(name='URL', value=generate_url(notification.game.slug), inline=True)
    embed.add_field(name='Turn Number', value=notification.turn, inline=True)
    if notification.game.remindinterval and not notification.game.muted:
        lastping = notification.lastnotified if notification.lastnotified else datetime.now()
        nextping = (lastping + timedelta(seconds=notification.game.remindinterval)).timestamp()
        embed.add_field(
            name='Next ping',
            value=f'<t:{int(nextping)}:R>',
            inline=True)
    if not notification.player.discordid:
        embed.set_footer(text=('Is this you? Click "This is me" to associate this player with your '
    'Discord account so you can get pinged directly on future turns.'))
    else:
        embed.set_footer(text=("If this player is linked to the wrong person, or the person it's "
            "linked to doesn't want to pe pinged, click \"Unlink player\" below."))
    embed.timestamp = datetime.now()
    return embed

def get_view(notification: TurnNotification) -> View:
    '''
    Gets the initial view for a turn notification.
    '''
    return View(
        PlayerLinkButton(
            notification.player,
            notification.game),
        MuteButton(notification.game))
