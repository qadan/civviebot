'''
Loads and works with configs potentially passed in from the environment.
'''

import logging
import logging.config as logging_config
from os import environ, access, R_OK
from dotenv import load_dotenv
from yaml import load, SafeLoader

logger = logging.getLogger(f'civviebot.{__name__}')


def add_dotenv():
    '''
    Adds the dotenv to the environ variables.
    '''
    load_dotenv(environ.get('DOTENV_PATH', None))


add_dotenv()


DISCORD_CLIENT_ID = environ.get('DISCORD_CLIENT_ID', None)
if not DISCORD_CLIENT_ID:
    raise ValueError('DISCORD_CLIENT_ID cannot be None')
COMMAND_PREFIX = environ.get('COMMAND_PREFIX', 'c6')
MIN_TURNS = int(environ.get('MIN_TURNS', 10))
NOTIFY_INTERVAL = int(environ.get('NOTIFY_INTERVAL', 5))
REMIND_INTERVAL = int(environ.get('REMIND_INTERVAL', 604800))
STALE_GAME_LENGTH = int(environ.get('STALE_GAME_LENGTH', 2592000))
NOTIFY_LIMIT = int(environ.get('NOTIFY_LIMIT', 100))
CLEANUP_INTERVAL = int(environ.get('CLEANUP_INTERVAL', 86400))
CLEANUP_LIMIT = int(environ.get('CLEANUP_LIMIT', 1000))
USE_FULL_NAMES = bool(environ.get('USE_FULL_NAMES', False))
_DEBUG_GUILD = environ.get('DEBUG_GUILD', None)
DEBUG_GUILDS = [int(_DEBUG_GUILD)] if _DEBUG_GUILD else []
CIVVIEBOT_HOST = environ.get('CIVVIEBOT_HOST', 'localhost')
LOGGING_CONFIG = environ.get('LOGGING_CONFIG', 'logging.yml')
CIVVIEBOT_DB_DIALECT = environ.get('CIVVIEBOT_DB_DIALECT', 'postgresql')
CIVVIEBOT_DB_DRIVER = environ.get('CIVVIEBOT_DB_DRIVER', 'pg8000')
DB_URL_KWARGS = {
    key[17:].lower(): environ.get(key)
    for key in environ
    if key[:17] == 'CIVVIEBOT_DB_URL_'
}
# Stash a copy of the endpoint.
_FULL_HOST = (CIVVIEBOT_HOST[:-1]
              if CIVVIEBOT_HOST[-1] == '/'
              else CIVVIEBOT_HOST)
if CIVVIEBOT_HOST[0:7] != 'http://' and CIVVIEBOT_HOST[0:8] != 'https://':
    _FULL_HOST = 'http://' + CIVVIEBOT_HOST
API_ENDPOINT = _FULL_HOST + '/civ6/'


def initialize_logging():
    '''
    Standardized logging initialization.
    '''
    if not access(LOGGING_CONFIG, R_OK):
        raise PermissionError(f'Cannot read config from {LOGGING_CONFIG}')
    with open(LOGGING_CONFIG, encoding='utf-8') as log_config:
        log_config = load(log_config, Loader=SafeLoader)
    logging_config.dictConfig(log_config)
