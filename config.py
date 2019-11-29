import requests
from os import path
from yaml import load as yaml_load

class CivvieBotConfig():
	'''
	Encapsulates a CivvieBot configuration.
	'''

	config = None

	def __init__(self):
		'''
		Gets the .yaml configuration as a dict.
		'''
		config_file = path.dirname(path.realpath(__file__)) + '/config.yml'

		if not path.isfile(config_file):
			raise FileNotFoundError(f'The config.yml could not be found or read in {config_file}.')

		with open(config_file, 'r') as loaded_config:
			self.config = yaml_load(loaded_config)

	def get(self, key):
		return self.config[key]