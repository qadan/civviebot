'''
Various utilities that format strings.
'''

from datetime import timedelta
from typing import List
from discord import User, Member
from utils import config


def expand_seconds(seconds: int | timedelta) -> str:
    '''
    Gets a string representing a number of seconds as hours, minutes and
    seconds.
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
        pluralize('second', int(seconds))
    )
    return ', '.join([bit for bit in bits if bit[0] != '0'])


def get_display_name(user: User | Member) -> str:
    '''
    Returns the appropriate display name for a user or member.
    '''
    return user.display_name if config.USE_FULL_NAMES else user.name


def pluralize(word: str, quantity: int | List) -> str:
    '''
    Markedly English and incomplete implementation of pluralization.

    As implemented, this only appends an 's' if the quantity isn't 1. This is
    fine for a bot that is only written in English, doesn't support
    localization, and is only actually pluralizing a few words like 'game' and
    'player'. Something more appropriate can be made if any of these
    stipulations no longer hold.

    This doc comment is already way too long for what this does but I feel it
    somewhat important to acknowledge.
    '''
    if not isinstance(quantity, int):
        quantity = len(quantity)
    return f'{str(quantity)} {word}{"s"[:quantity^1]}'
