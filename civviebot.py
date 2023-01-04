'''
Discord bot and webhook API for Civilization 6 turn notifications.
'''

from bot.civviebot import civviebot
from utils import config
from utils.utils import initialize_logging

if __name__ == '__main__':
    initialize_logging()
    civviebot.run(config.DISCORD_TOKEN)
