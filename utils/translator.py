from random import choice


class CivvieBotTranslator():
    '''
    Translator for turning Civ VI JSON into Discord Webhook JSON.
    '''

    config = None

    def __init__(self, config):
        self.config = config

    def get_discord_id_for(self, name):
        '''
        Gets the string to use to ping a Discord ID if the given name is mapped
        in the configs.
        '''
        if name in self.config.get('user_map'):
            return "<@{id}>".format(id=self.config.get('user_map')[name])
        return None

    def map_discord_id(self, message):
        '''
        Potentially jams a Discord ID into the message.
        '''
        discord_id = self.get_discord_id_for(message['value2'])
        message['value2'] = discord_id or message['value2']
        return message

    def get_discord_webhook_json(self, civ_data):
        '''
        Turns Civ VI data into a message.
        '''
        message = choice(self.config.get('phrases'))
        # @TODO: potentially unnecessary? Don't really know what comes back from
        # Firaxis in the JSON; should re-evaluate later.
        message['value3'] = str(message['value3'])
        translated_data = self.map_discord_id(civ_data)
        return {
            'content': message.format(**translated_data),
        }
