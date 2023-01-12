'''
Builders for portions of messages dealing with turn notification.
'''

import logging
from datetime import datetime
from discord import Embed
from sqlalchemy import select
from database.models import WebhookURL, TurnNotification
from database.utils import get_session
from utils.utils import generate_url
from bot.interactions.common import View
from bot.interactions.notify import MuteButton, PlayerLinkButton

logger = logging.getLogger(f'civviebot.{__name__}')

def get_content(turn: TurnNotification) -> str:
    '''
    Gets the content for a turn notification message.
    '''
    tag = f'<@{turn.player.discordid}>' if turn.player.discordid else turn.player.name
    message = (f"It's {tag}'s turn!"
        if not turn.lastnotified
        else f"**Reminder**: it's {tag}'s turn (<t:{int(turn.logtime.timestamp())}:R>)")
    if turn.game.webhookurl.limitwarned is False:
        message += (f"\n\n**NOTICE**: I'm now tracking 25 games via the URL "
            f"{generate_url(turn.slug)}. If any new games are created, I'll have to ignore them. "
            "You'll either need to remove some games manually, or if none of them should be, "
            'create a new webhook URL.')
        with get_session() as session:
            url: WebhookURL = session.scalar(
                select(WebhookURL).where(WebhookURL.slug == turn.slug))
            if not url:
                logger.error(('Tried to load the webhook URL %s to set the warnedlimit, but it no '
                    'longer seems to exist'),
                    turn.slug)
                return message
            url.limitwarned = True
    return message

def get_embed(turn: TurnNotification) -> Embed:
    '''
    Gets the embed for a turn notification message.
    '''
    embed = Embed(title=turn.game.name)
    embed.add_field(
        name='Current Player',
        value=turn.player.name,
        inline=True)
    embed.add_field(name='URL', value=generate_url(turn.slug), inline=True)
    embed.add_field(name='Turn Number', value=turn.turn, inline=True)
    if turn.game.remindinterval and not turn.game.muted:
        embed.add_field(
            name='Next ping',
            value=f'<t:{int(turn.lastnotified + turn.game.remindinterval)}:R>',
            inline=True)
    if not turn.player.discordid:
        embed.set_footer(text=('Is this you? Click "This is me" to associate this player with your '
    'Discord account so you can get pinged directly on future turns.'))
    else:
        embed.set_footer(text=("If this player is linked to the wrong person, or the person it's "
            "linked to doesn't want to pe pinged, click \"Unlink player\" below."))
    embed.timestamp = datetime.now()
    return embed

def get_view(turn: TurnNotification) -> View:
    '''
    Gets the initial view for a turn notification.
    '''
    return View(PlayerLinkButton(turn.player, turn.game), MuteButton(turn.game))
