'''
Error classes and methods to use with exceptions.
'''

import logging
from collections.abc import Coroutine
from traceback import extract_tb, format_list
from discord import Interaction

logger = logging.getLogger(f'civviebot.{__name__}')


class ValueAccessError(Exception):
    '''
    Exception raised when the value of a component is accessed before being
    set.
    '''


class NoPlayersError(ValueError):
    '''
    Error to throw when players can't be found.
    '''


class NoGamesError(ValueError):
    '''
    Error to throw when games can't be found.
    '''


async def base_error(log_instance: logging.Logger,
                     error: Exception,
                     interaction: Interaction = None):
    '''
    Base error and response to use. Requires the file calling this to pass its
    logger in.
    '''
    log_instance.error(
        'Unexpected failure: %s: %s\n%s',
        error.__class__.__name__,
        error,
        ''.join(format_list(extract_tb(error.__traceback__)))
    )
    if interaction:
        await interaction.response.edit_message(
            content=(
                'An unknown error occurred; contact an administrator if this '
                'persists.'
            ),
            embed=None,
            view=None
        )


def handle_callback_errors(func: Coroutine) -> Coroutine:
    '''
    Decorator; wraps callback functions for classes that don't have an on_error
    implementation, allowing errors to be handled by that class's on_error().
    '''
    async def _decorator(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        # We're simply passing it along, so generalized exception is fine.
        except Exception as error:
            interaction = None
            for arg in args:
                if isinstance(arg, Interaction):
                    interaction = arg
                if not interaction:
                    logger.warning(
                        (
                            'Function %s decorated with '
                            '@handle_callback_errors does not include an '
                            'Interaction object; no message will be passed to '
                            'the user as a result of this error.'
                        ),
                        func.__name__
                    )
            if not args:
                logger.warning(
                    (
                        'Function %s decorated with @handle_callback_errors '
                        'is not a class method'
                    ),
                    func.__name__
                )
                await base_error(logger, error, interaction=interaction)
            elif not hasattr(args[0], 'on_error'):
                logger.warning(
                    (
                        'Function %s decorated with @handle_callback_errors '
                        'does not implement on_error'
                    ),
                    func.__name__
                )
                await base_error(logger, error, interaction=interaction)
            else:
                # A bit permissive but we're expecting it to be used correctly.
                await args[0].on_error(error, args[1])

    return _decorator
