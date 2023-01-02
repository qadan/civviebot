'''
Error classes and methods to use with exceptions.
'''

from logging import Logger
from traceback import extract_tb, format_list
from discord import Interaction

class ValueAccessError(Exception):
    '''
    Exception raised when the value of a component is accessed before being set.
    '''

class NoPlayersError(ValueError):
    '''
    Error to throw when players can't be found.
    '''

class NoGamesError(ValueError):
    '''
    Error to throw when games can't be found.
    '''

async def base_error(logger: Logger, error: Exception, interaction: Interaction):
    '''
    Base error and response to use. Requires the file calling this to pass its logger in.
    '''
    logger.error(
        'Unexpected failure: %s: %s\n%s',
        error.__class__.__name__,
        error,
        ''.join(format_list(extract_tb(error.__traceback__))))
    await interaction.response.edit_message(
        content=('An unknown error occurred; contact an administrator if this persists.'),
        embed=None,
        view=None)
