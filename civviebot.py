'''
Discord bot and webhook API for Civilization 6 turn notifications.
'''

import logging
from bot.civviebot import civviebot
from utils import config
from utils.utils import initialize_logging

if __name__ == '__main__':
    initialize_logging()
    logger = logging.getLogger(__name__)
    try:
        civviebot.run(config.DISCORD_TOKEN)
    except RuntimeError as runtime_error:
        error_message = str(runtime_error)
        if 'Event loop is closed' != error_message:
            logger.error(runtime_error)
    finally:
        logger.info('Shut down CivvieBot')
