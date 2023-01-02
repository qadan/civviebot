'''
Loads and works with configs potentially passed in from the environment.
'''

from os import environ

# Load .env variables.
_DOTENV = environ.get('dotenv', None)
if _DOTENV:
    from dotenv import load_dotenv
    load_dotenv(_DOTENV)

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
SQLITE_DATABASE = environ.get('SQLITE_DATABASE', './database.sqlite')
LOGGING_CONFIG = environ.get('LOGGING_CONFIG', './logging.yml')
DEVEL_PORT = environ.get('DEVEL_PORT', None)
