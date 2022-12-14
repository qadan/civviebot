'''
Miscellaneous utilities used in various spots that I couldn't think to put elsewhere.
'''

from collections.abc import Coroutine
from hashlib import sha1
from time import time
from discord import User, Interaction, Member
from . import config


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
    def to_tuple(string, count):
        return (string + 's' if count != 1 else string, count)
    hours = int(seconds / 60 / 60)
    seconds -= hours * 3600
    minutes = int(seconds / 60)
    seconds -= minutes * 60
    bits = (
        to_tuple('hour', hours),
        to_tuple('minute', minutes),
        to_tuple('second', int(seconds)),
    )
    return ', '.join(
        [f'{bit[1]} {bit[0]}' for bit in bits if bit[1]])


def get_discriminated_name(user: User | Member | None) -> str:
    '''
    Returns the 'name#discriminator' form of a User's name.
    '''
    if user is not None:
        return user.name + '#' + user.discriminator
    raise TypeError('User passed to get_discriminated_name is not a User or Member')


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
    allowing errors to be handled by that class's on_error.
    '''
    async def _decorator(*args, **kwargs):
        if len(args) != 2:
            raise AttributeError(
                ('Method handle_callback_errors may only be used to decorate a class method with '
                    'two arguments - the class itself and an Interaction'))
        on_error = getattr(args[0], 'on_error', None)
        if not callable(on_error):
            raise TypeError(
                'Method handle_callback_errors may only be used to decorate class methods.')
        if not isinstance(args[1], Interaction):
            raise TypeError(
                ('Method handle_callback_errors may only be used to decorate a class method whose '
                    'second argument is an Interaction'))

        try:
            await func(*args, **kwargs)
        # Ignoring as we're simply passing the error along.
        except Exception as error: # pylint: disable=broad-except
            await args[0].on_error(error, args[1])

    return _decorator
