'''
Builders for portions of messages dealing with turn notification.
'''

import logging
from datetime import datetime
from discord import Embed
from pony.orm import db_session, ObjectNotFound
from database import models
from utils.utils import generate_url
from bot.cogs.game import NAME as game_prefix
from bot.interactions.common import View
from bot.interactions.notify import MuteButton, PlayerLinkButton

NO_EMBED_FOOTER = '''Is this you? Click "This is me" to associate this player with your Discord
username so you can get pinged on future turns.'''
EMBED_FOOTER = '''If you would like to stop getting pinged, click "Unlink me" below.'''

logger = logging.getLogger(f'civviebot.{__name__}')

def get_content(game: models.Game) -> str:
    '''
    Gets the content for a turn notification message.
    '''
    tag = f'<@{game.lastup.discordid}>' if game.lastup.discordid else game.lastup.playername
    message = f"It's {tag}'s turn!"
    if game.webhookurl.warnedlimit is False:
        message += (f"\n\n**NOTICE**: I'm now tracking 25 games via the URL "
            f"{generate_url(game.webhookurl.slug)}. If any new games are created, I'll have to "
            "ignore them. You'll either need to remove some games manually using"
            f'`/{game_prefix}_manage delete`, or if none of them should be, create a new webhook '
            'URL.')
        with db_session():
            try:
                whurl = models.WebhookURL[game.webhookurl.slug]
            except ObjectNotFound:
                logger.error(('Tried to load the webhook URL %s to set the warnedlimit, but it no'
                    'longer seems to exist'),
                    game.webhookurl.slug)
            whurl.warnedlimit = True
    return message


def get_embed(game: models.Game) -> Embed:
    '''
    Gets the embed for a turn notification message.
    '''
    webhook_url = generate_url(game.webhookurl.slug)
    embed = Embed(
        title=webhook_url,
        description='Game Information:',
        # Looking forward to this exploding in some long-ass game.
        color=game.turn * 100)
    embed.add_field(
        name='Current Player',
        value=game.lastup.playername,
        inline=True)
    embed.add_field(name='Game', value=game.gamename, inline=True)
    embed.add_field(name='Turn Number', value=game.turn, inline=True)
    if not game.lastup.discordid:
        embed.set_footer(text=NO_EMBED_FOOTER)
    else:
        embed.set_footer(text=EMBED_FOOTER)
    embed.timestamp = datetime.now()
    return embed


def get_view(game: models.Game) -> View:
    '''
    Gets the initial view for a turn notification.
    '''
    return View(
        PlayerLinkButton(game.lastup.id, game.id),
        MuteButton(game.id))
