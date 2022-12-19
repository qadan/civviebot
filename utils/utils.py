'''
Miscellaneous utilities used in various spots that I couldn't think to put elsewhere.
'''

from collections.abc import Coroutine
from hashlib import sha1
from time import time
from typing import List
from discord import User, Member, ChannelType
from pony.orm.core import Collection
from . import config


# Channel types that CivvieBot is willing to track games in.
VALID_CHANNEL_TYPES = [ChannelType.text, ChannelType.public_thread, ChannelType.private_thread]


def generate_url(slug) -> str:
    '''
    De-facto implementation of URL generation.
    '''
    url = config.get('app_url')
    url = url[:-1] if url[-1] == '/' else url
    return config.get('app_url') + ':' + str(config.get('port')) + '/civ6/' + slug


def expand_seconds_to_string(seconds: int) -> str:
    '''
    Gets a string representing a number of seconds as hours, minutes and seconds.
    '''
    hours = int(seconds / 60 / 60)
    seconds -= hours * 3600
    minutes = int(seconds / 60)
    seconds -= minutes * 60
    bits = (
        pluralize('hour', hours),
        pluralize('minute', minutes),
        pluralize('second', int(seconds)))
    return ', '.join([bit for bit in bits if bit[0] != '0'])


def get_discriminated_name(user: User | Member) -> str:
    '''
    Returns the 'name#discriminator' form of a User's name.
    '''
    return user.name + '#' + user.discriminator


def generate_slug() -> str:
    '''
    Generates a slug for use with webhook URLs.

    Slugs are 12 character hex strings generated from the current Unix timestamp.
    '''
    hasher = sha1(str(time()).encode('UTF-8'))
    return hasher.hexdigest()[:12]


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
