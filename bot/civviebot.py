'''
Contains civviebot, the standard implementation of CivvieBot.
'''

import logging
from discord import Intents, AllowedMentions
from discord.ext import commands

DESCRIPTION = '''
Manages Discord messaging and webhook handling for Civilization 6 games.

Used to allow Civilization 6 itself to inform users of their turn.
'''

intents = Intents.default()
intents.members = True # pylint: disable=assigning-non-slot

civviebot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description=DESCRIPTION,
    intents=intents,
    allowed_mentions=AllowedMentions(
        everyone=False,
        users=True,
        roles=False),
    debug_guilds=[473479072949731338])


civviebot.load_extension("bot.cogs.base")
civviebot.load_extension("bot.cogs.cleanup")
civviebot.load_extension("bot.cogs.game")
civviebot.load_extension("bot.cogs.notify")
civviebot.load_extension("bot.cogs.player")
civviebot.load_extension("bot.cogs.webhookurl")


@civviebot.event
async def on_ready():
    '''
    Responds to the on_ready event.
    '''
    logging.info('%s ready (ID: %d)', civviebot.user, civviebot.user.id)
    if civviebot.debug_guilds:
        logging.info(
            'CivvieBot is running with set debug_guilds. Global commands will not be created.')
