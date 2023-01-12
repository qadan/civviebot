'''
Builders for portions of messages dealing with games.
'''

from time import time
from discord import Embed
from sqlalchemy import select, func
from database.models import Game
from database.utils import get_session
from utils import config
from utils.utils import expand_seconds_to_string, generate_url

CLEANUP_CONTENT = 'Information about the game cleanup schedule:'

def get_info_embed(game: Game):
    '''
    Gets the embed to provide info about a game.
    '''
    embed = Embed(title=game.name)
    embed.add_field(name='Current turn:', value=game.turns[0].turn, inline=True)
    embed.add_field(name='Current player:', value=game.turns[0].playername, inline=True)
    embed.add_field(
        name='Most recent turn:',
        value=f'<t:{int(game.turns[0].logtime.timestamp())}:R>',
        inline=True)
    if game.remindinterval and game.turns[0].turn > game.minturns and not game.muted:
        embed.add_field(
            name='Next reminder:',
            value=('<t:'
                + str(int(game.remindinterval + game.turns[0].lastnotified))
                + '>'),
            inline=True)
    embed.add_field(name='Notifies after:', value=f'Turn {game.minturns}', inline=True)
    embed.add_field(name='Is muted:', value='Yes' if game.muted else 'No', inline=True)
    embed.add_field(name='Tracked players:', value=len(game.players), inline=True)
    embed.add_field(name='Webhook URL:', value=generate_url(game.webhookurl.slug))
    embed.set_footer(text=('If you\'re part of this game, place the above webhook URL in your '
        'Civilization 6 settings to send notifications to CivvieBot when you take your turn '
        f'(use "/{config.COMMAND_PREFIX} quickstart" for more setup information). For a list '
        f'of known players in this game, use "/{config.COMMAND_PREFIX}game players".'))
    return embed

def get_cleanup_embed(channel: int) -> Embed:
    '''
    Gets the embed for displaying cleanup information.
    '''
    embed = Embed(title='Cleanup schedule and statistics:')
    embed.description = ('During cleanup, games that are considered "stale" are deleted. When '
        'a game is deleted by any means, its players are marked to be deleted, which also '
        'occurs during cleanup.')
    embed.add_field(
        name='A game is considered stale:',
        value=f'{expand_seconds_to_string(config.STALE_GAME_LENGTH)} after the last '
        'received notification')
    embed.add_field(
        name='Cleanup occurs every:',
        value=expand_seconds_to_string(config.CLEANUP_INTERVAL))
    embed.add_field(
        name='Cleanup removes:',
        value=f'{config.CLEANUP_LIMIT} of each type of record')
    with get_session() as session:
        stale_games = session.scalar(select(func.count()).select_from(Game).where(
            Game.turns[0].logtime.total_seconds() + config.STALE_GAME_LENGTH < time()
            and Game.webhookurl.channelid == channel))
    embed.add_field(name='Current stale games:', value=stale_games)
    return embed
