'''
Loads and works with configs potentially passed in from the environment.
'''

import logging
from os import access, R_OK, environ
from dotenv import load_dotenv
from yaml import load, SafeLoader

logger = logging.getLogger(f'civviebot.{__name__}')

load_dotenv()

COMMAND_PREFIX = environ.get('COMMAND_PREFIX', 'c6')
MIN_TURNS = int(environ.get('MIN_TURNS', 10))
NOTIFY_INTERVAL= float(environ.get('NOTIFY_INTERVAL', 5.0))
STALE_NOTIFY_INTERVAL = float(environ.get('STALE_NOTIFY_INTERVAL', 604800.0))
STALE_GAME_LENGTH = float(environ.get('STALE_GAME_LENGTH', 2592000.0))
NOTIFY_LIMIT = int(environ.get('NOTIFY_LIMIT', 100))
CLEANUP_INTERVAL = float(environ.get('CLEANUP_INTERVAL', 86400.0))
CLEANUP_LIMIT = int(environ.get('CLEANUP_LIMIT', 1000))
DEBUG_GUILDS = []
_DEBUG_GUILD = environ.get('DEBUG_GUILD', None)
if _DEBUG_GUILD:
    DEBUG_GUILDS.append(int(_DEBUG_GUILD))
CIVVIEBOT_HOST = environ.get('CIVVIEBOT_HOST', 'localhost')
LOGGING_CONFIG = environ.get('LOGGING_CONFIG', 'logging.yml')

_DB_LOCATION = environ.get('DATABASE_CONFIG', 'db_config.yml')
if not access(_DB_LOCATION, R_OK):
    raise PermissionError(f'Cannot read database config from {_DB_LOCATION}')
with open(_DB_LOCATION, 'r', encoding='utf-8') as db_config:
    DATABASE_CONFIG = load(db_config, Loader=SafeLoader)