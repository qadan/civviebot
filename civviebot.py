'''
Discord bot and webhook API for Civilization 6 turn notifications.
'''

import asyncio
import logging
import logging.config as logging_config
from os import access, R_OK
from signal import Signals
from yaml import load, SafeLoader
import database.models
from bot.civviebot import civviebot
from api.civviebot_api import civviebot_api

# Initialize logging.
try:
    from utils import config
except PermissionError as file_error:
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    handler = logging.StreamHandler(stream='ext://sys.stdout', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter(
        "[{asctime}] [{levelname} - {name}]: {message}",
        style=logging.StrFormatStyle))
    logger.addHandler(handler)
    logger.error(file_error)
log_config_path = config.get_path('logging')
if not access(log_config_path, R_OK):
    raise PermissionError(f'Cannot read configuration from {log_config_path}')
with open(config.get_path('logging'), 'r') as log_config:
    log_config = load(log_config, Loader=SafeLoader)
logging_config.dictConfig(log_config)

logger = logging.getLogger(__name__)

async def shutdown(signal: Signals, loop: asyncio.AbstractEventLoop):
    '''
    Shutdown function on reciept of the given signal.
    '''
    logger.info('Received %s; shutting down...', signal.name)
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info('Ending main loop ...')
    loop.stop()


def main():
    '''
    Main application loop.
    '''
    database.models.db.generate_mapping(create_tables=True)
    loop = asyncio.get_event_loop_policy().get_event_loop()
    for signal in (Signals.SIGINT, Signals.SIGHUP, Signals.SIGTERM):
        loop.add_signal_handler(signal, lambda s=signal: asyncio.create_task(shutdown(s, loop)))

    try:
        loop.create_task(civviebot.start(config.get('discord_token')))
        loop.create_task(civviebot_api.run(
            host='127.0.0.1',
            port=config.get('port'),
            use_reloader=False,
            loop=loop))
        loop.run_forever()
    except RuntimeError as runtime_error:
        error_message = str(runtime_error)
        if 'Event loop is closed' != error_message:
            logger.error(runtime_error)
    finally:
        loop.close()
        logger.info('Successfully shut down CivvieBot')


if __name__ == '__main__':
    main()
