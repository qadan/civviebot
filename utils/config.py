'''
Loads and works with the config found in config.yml.

A configuration can be passed in as the CIVVIEBOT_CONFIG environment variable.

Importing the module raises a FileNotFoundError or PermissionError if config.yml could not be found
or read from.
'''

from os import path, environ, access, R_OK, W_OK
from yaml import load, SafeLoader

CONFIG = None
config_file = environ.get(
    'CIVVIEBOT_CONFIG',
    path.join(path.dirname(path.realpath(__file__)), '..', 'config.yml'))

if not access(config_file, R_OK):
    raise PermissionError(
        f'Cannot read configuration from {config_file}')

with open(config_file, 'r', encoding='UTF-8') as loaded_config:
    CONFIG = load(loaded_config, Loader=SafeLoader)

def get(key, default=None):
    '''
    Get a value from the root of the configuration YAML.
    '''
    return CONFIG[key].strip() if key in CONFIG else default


def get_env_path():
    '''
    Gets a path from a value in the CIVVIEBOT_PATH (or the base folder of CivvieBot).
    '''
    env_path = environ.get(
        'CIVVIEBOT_PATH',
        path.join(path.dirname(path.realpath(__file__)), '..'))
    if not access(env_path, R_OK | W_OK):
        raise PermissionError(f'''The path CivvieBot needs to create files like the database
            ({env_path}) is missing read/write permissions''')
    return env_path


def get_path(key):
    '''
    Get a path from the 'path' section of the configuration YAML.

    This will either be the folder one level up from this file, or can be set using the environment
    variable CIVVIEBOT_PATH.
    '''
    return path.join(get_env_path(), CONFIG['paths'][key].strip())
