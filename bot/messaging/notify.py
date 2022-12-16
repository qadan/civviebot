'''
Builders for portions of messages dealing with turn notification.
'''

from datetime import datetime
from discord import Embed
from discord.ui import View
from database import models
from utils.utils import generate_url
from bot.interactions.notify import MuteButton, PlayerLinkButton

NO_EMBED_FOOTER = '''Is this you? Click "This is me" to associate this player with your Discord
username so you can get pinged on future turns.'''
EMBED_FOOTER = '''If you would like to stop getting pinged - temporarily or otherwise - click
"Unlink me" below.'''


def get_content(player: models.Player) -> str:
    '''
    Gets the content for a turn notification message.
    '''
    tag = f'<@{player.discordid}>' if player.discordid else player.playername
    return f"It's {tag}'s turn!"


def get_embed(game: models.Game) -> Embed:
    '''
    Gets the embed for a turn notification message.
    '''
    webhook_url = generate_url(game.webhookurl.slug)
    embed = Embed(
        title=webhook_url,
        description='Game Information:',
        # Looking forward to this exploding in some long-ass game.
        color=game.turn * 100,
    )
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
