from random import choice

class CivvieBotTranslator():
	'''
	Translator for turning Civ VI JSON into Discord Webhook JSON.
	'''

	phrases = []
	user_map = {}

	def __init__(self, config):
		self.phrases = config.get('phrases')
		self.user_map = config.get('user_map')


	def get_discord_id_for(self, name):
		'''
		Gets the Discord ID for a username, if it's in the config.
		'''
		if name in self.user_map:
		    return "<@{id}>".format(id=self.user_map[name])
		return None


	def map(self, message):
		'''
		Mapper from Civ VI's weird values to something more sensible to describe
		in the config.yml
		'''
		name = self.get_discord_id_for(message['value2']) or message['value2']
		return {
			"game": message['value1'],
			"user": name,
			"turn": message['value3'],
		}


	def string_replace(self, string, message):
		'''
		Simple helper to run the replacement and return the formatted string.
		'''
		mapped_message = self.map(message)
		return string.format(**mapped_message)


	def get_content(self, translated_data):
		'''
		Turns translated data into a message.
		'''
		to_send = choice(self.phrases)
		return {
			'content': to_send.format(**translated_data)
		}