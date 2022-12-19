'''
Contains civviebot, the standard implementation of CivvieBot.
'''

import logging
from discord import Intents, AllowedMentions, Guild
from discord.ext import commands
from pony.orm import db_session, ObjectNotFound, left_join
from database import models
from utils import config
from utils.utils import pluralize

DESCRIPTION = '''
Manages Discord messaging and webhook handling for Civilization 6 games.

Used to allow Civilization 6 itself to inform users of their turn.
'''

intents = Intents.default()
intents.members = True # pylint: disable=assigning-non-slot

debug_guild = config.get('debug_guild', None)
civviebot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description=DESCRIPTION,
    intents=intents,
    allowed_mentions=AllowedMentions(
        everyone=False,
        users=True,
        roles=False),
    debug_guilds=[debug_guild] if debug_guild is not None else debug_guild)


civviebot.load_extension("bot.cogs.base")
civviebot.load_extension("bot.cogs.cleanup")
civviebot.load_extension("bot.cogs.game")
civviebot.load_extension("bot.cogs.notify")
civviebot.load_extension("bot.cogs.player")
civviebot.load_extension("bot.cogs.webhookurl")

@civviebot.event
async def on_guild_join(guild: Guild):
    '''
    Establishes the Guild entry in the database for this guild.
    '''
    with db_session():
        try:
            # This should not happen but y'know how it be.
            models.GuildSettings[str(guild.id)]
        except ObjectNotFound:
            models.GuildSettings(guildid=str(guild.id))
            logging.info('Created empty guild settings for new guild: %d', guild.id)


@civviebot.event
async def on_guild_remove(guild: Guild):
    '''
    Purge everything from the database pertaining to this guild.
    '''
    players = 0
    urls = 0
    with db_session():
        for channel in guild.channels:
            for player in left_join(p for p in models.Player for g in p.games if
                g.webhookurl.channelid == channel.id):
                try:
                    player.delete = True
                except ObjectNotFound:
                    pass
                players += 1
            for url in models.WebhookURL.select(channelid=channel.id):
                try:
                    url.delete = True
                except ObjectNotFound:
                    pass
                urls += 1
        try:
            guild_settings = models.GuildSettings[str(guild.id)]
            guild_settings.delete()
        except ObjectNotFound:
            pass
    logging.info(('CivvieBot was removed from guild %d; %s and %s, as well as attached games, were '
        'flagged to be removed.'),
        guild.id,
        pluralize('associated player', players),
        pluralize('associated webhook URL', urls))


@civviebot.event
async def on_ready():
    '''
    Responds to the on_ready event.
    '''
    logging.info('%s ready (ID: %d)', civviebot.user, civviebot.user.id)
    if civviebot.debug_guilds:
        logging.info(
            'CivvieBot is running with set debug_guilds. Global commands will not be created.')
