'''
Discord bot and webhook API for Civilization 6 turn notifications.
'''

from os import environ
from bot.civviebot import civviebot
from database.utils import emit_all
from utils.config import initialize_logging, add_dotenv

if __name__ == '__main__':
    initialize_logging()
    emit_all()
    add_dotenv()
    civviebot.run(environ.get('DISCORD_TOKEN'))
