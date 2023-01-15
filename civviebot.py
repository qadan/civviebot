'''
Discord bot and webhook API for Civilization 6 turn notifications.
'''

from bot.civviebot import civviebot
from database.utils import emit_all
from utils import config
from utils.config import initialize_logging

if __name__ == '__main__':
    initialize_logging()
    emit_all()
    civviebot.run(config.DISCORD_TOKEN)
