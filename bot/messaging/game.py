'''
Builders for portions of messages dealing with games.
'''

from time import time
from discord import Embed
from pony.orm import db_session, count
from database.models import Game, Player, WebhookURL
from utils import config
from utils.utils import expand_seconds_to_string


CONTENT = 'Information about the game cleanup schedule:'


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
        value=f'{expand_seconds_to_string(config.get("stale_game_length"))} after the last '
        'received notification')
    embed.add_field(
        name='Cleanup occurs every:',
        value=expand_seconds_to_string(config.get('cleanup_interval')))
    embed.add_field(
        name='Cleanup removes:',
        value=f'{config.get("cleanup_limit")} of each type of record')
    with db_session():
        embed.add_field(
            name='Current stale games:',
            value=count(g for g in Game 
                if g.lastturn + config.get('stale_game_length') < time()
                and g.webhookurl.channelid == channel))
        embed.add_field(
            name='Players slated to be deleted:',
            value=count(
                p for p in Player for g in p.games
                if p.cleanup is True
                and g.webhookurl.channelid == channel))
    return embed