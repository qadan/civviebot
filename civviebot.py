'''
Discord bot and webhook API for Civilization 6 turn notifications.
'''

import asyncio
import logging
import logging.config
from signal import SIGHUP, SIGTERM, SIGINT
import database.models
from bot.civviebot import civviebot
from api.civviebot_api import civviebot_api


try:
    from utils import config
except PermissionError as file_error:
    logging.error(file_error)

logging.config.fileConfig(config.get_path('logging'))


async def shutdown(signal, loop):
    '''
    Shutdown function on reciept of the given signal.
    '''
    logging.info('Received %s; shutting down...', signal.name)
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    logging.info('Ending main loop ...')
    loop.stop()


def main():
    '''
    Main application loop.
    '''
    database.models.db.generate_mapping(create_tables=True)
    loop = asyncio.get_event_loop_policy().get_event_loop()
    for signal in (SIGINT, SIGHUP, SIGTERM):
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
            logging.error(runtime_error)
    finally:
        loop.close()
        logging.info('Successfully shut down CivvieBot')


if __name__ == '__main__':
    main()
