'''
Loads and works with configs potentially passed in from the environment.
'''

import logging
from os import environ
from dotenv import load_dotenv

logger = logging.getLogger(f'civviebot.{__name__}')

_DOTENV_PATH = environ.get('DOTENV_PATH', None)
load_dotenv(_DOTENV_PATH)

DISCORD_TOKEN = environ.get('DISCORD_TOKEN', None)
if not DISCORD_TOKEN:
    raise ValueError('DISCORD_TOKEN not set')
COMMAND_PREFIX = environ.get('COMMAND_PREFIX', 'c6')
MIN_TURNS = int(environ.get('MIN_TURNS', 10))
NOTIFY_INTERVAL= int(environ.get('NOTIFY_INTERVAL', 5))
REMIND_INTERVAL = int(environ.get('REMIND_INTERVAL', 604800))
STALE_GAME_LENGTH = int(environ.get('STALE_GAME_LENGTH', 2592000))
NOTIFY_LIMIT = int(environ.get('NOTIFY_LIMIT', 100))
CLEANUP_INTERVAL = int(environ.get('CLEANUP_INTERVAL', 86400))
CLEANUP_LIMIT = int(environ.get('CLEANUP_LIMIT', 1000))
_DEBUG_GUILD = environ.get('DEBUG_GUILD', None)
DEBUG_GUILDS = [int(_DEBUG_GUILD)] if _DEBUG_GUILD else []
CIVVIEBOT_HOST = environ.get('CIVVIEBOT_HOST', 'localhost')
LOGGING_CONFIG = environ.get('LOGGING_CONFIG', 'logging.yml')
CIVVIEBOT_DB_DIALECT = environ.get('CIVVIEBOT_DB_DIALECT', 'mysql')
CIVVIEBOT_DB_DRIVER = environ.get('CIVVIEBOT_DB_DRIVER', 'pymysql')
DB_URL_KWARGS = {
    key[17:].lower(): environ.get(key)
    for key in environ
    if key[:17] == 'CIVVIEBOT_DB_URL_'}
