'''
Miscellaneous utilities used in various spots that I couldn't think to put elsewhere.

Some of these should, like, get moved somewhere less stupid.
'''

from collections.abc import Coroutine
from typing import List
from discord import User, Member, ChannelType
from pony.orm import left_join
from pony.orm.core import Collection

from database.models import Game
from . import config

# Channel types that CivvieBot is willing to track games in.
VALID_CHANNEL_TYPES = [ChannelType.text, ChannelType.public_thread, ChannelType.private_thread]
# Caching some URL values as they're static.
_HOST = config.CIVVIEBOT_HOST
HOST = _HOST[:-1] if _HOST[-1] == '/' else _HOST
if HOST[0:7] != 'http://' and HOST[0:8] != 'https://':
    HOST = 'http://' + HOST
_PORT = config.CIVVIEBOT_PORT
PORT = f':{_PORT}' if _PORT else ''
API_ENDPOINT = HOST + PORT + '/civ6/'

def generate_url(slug) -> str:
    '''
    Gets the API endpoint URL for a given webhook URL slug.
    '''
    return API_ENDPOINT + slug

def expand_seconds_to_string(seconds: int) -> str:
    '''
    Gets a string representing a number of seconds as hours, minutes and seconds.
    '''
    def remove_unit(denominator):
        nonlocal seconds
        amount = int(seconds / denominator)
        seconds -= amount * denominator
        return amount

    bits = (
        pluralize('day', remove_unit(86400)),
        pluralize('hour', remove_unit(3600)),
        pluralize('minute', remove_unit(60)),
        pluralize('second', int(seconds)))
    return ', '.join([bit for bit in bits if bit[0] != '0'])

def get_discriminated_name(user: User | Member) -> str:
    '''
    Returns the 'name#discriminator' form of a User's name.
    '''
    return user.name + '#' + user.discriminator

def handle_callback_errors(func: Coroutine) -> Coroutine:
    '''
    Decorator; wraps callback functions for classes that don't have an on_error implementation,
    allowing errors to be handled by that class's on_error().
    '''
    async def _decorator(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        # Ignoring as we're simply passing the error along.
        except Exception as error: # pylint: disable=broad-except
            await args[0].on_error(error, args[1])

    return _decorator

def pluralize(word: str, quantity: int | List | Collection) -> str:
    '''
    Markedly English and incomplete implementation of pluralization.

    As implemented, this only appends an 's' if the quantity isn't 1. This is fine for a bot that
    is only written in English, doesn't support localization, and is only actually pluralizing a few
    words like 'game' 'player' and 'URL'. Something more appropriate can be made if any of these
    stipulations no longer hold.

    This doc comment is already way too long for what this does but I feel it somewhat important to
    acknowledge.
    '''
    if not isinstance(quantity, int):
        quantity = len(quantity)
    return f'{str(quantity)} {word}{"s"[:quantity^1]}'

def get_games_user_is_in(channel_id: int, user_id: int) -> List[Game]:
    '''
    Gets a list of Game entities the user is linked to a player in.
    '''
    return left_join(g for g in Game for p in g.players if
        g.webhookurl.channelid == channel_id and
        p in g.players and
        p.discordid == str(user_id))
