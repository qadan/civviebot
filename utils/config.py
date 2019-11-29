import requests
import yaml
from os import path, environ


class CivvieBotConfig():
    '''
    Encapsulates a CivvieBot configuration.
    '''

    config = None

    def __init__(self):
        '''
        Gets the .yaml configuration as a dict.
        '''
        config_file = environ.get(
                'CIVVIEBOT_CONFIG',
                path.dirname(path.realpath(__file__)) + '/../config.yml')

        if not path.isfile(config_file):
            raise FileNotFoundError(
                    f'config.yml could not be found or read in {config_file}.')
            exit(1)

        with open(config_file, 'r') as loaded_config:
            self.config = yaml.load(loaded_config, Loader=yaml.SafeLoader)

    def get(self, key):
        return self.config[key]
