'''
Contains civviebot, the standard implementation of CivvieBot.
'''

import logging
from traceback import extract_tb, format_list
from discord import Intents, AllowedMentions, Guild, ApplicationContext, ChannelType
from discord.abc import GuildChannel
from discord.errors import NotFound
from discord.ext.commands import Bot, errors as command_errors, when_mentioned_or
from discord.utils import get
from sqlalchemy import select, delete
from sqlalchemy.exc import NoResultFound
from database.models import WebhookURL, PlayerGames, Player, Game, TurnNotification
from database.connect import get_session
from utils import config
from utils.string import get_display_name

logger = logging.getLogger(f'civviebot.{__name__}')

DESCRIPTION = '''
Manages Discord messaging and webhook handling for Civilization 6 games.

Used to allow Civilization 6 itself to inform users of their turn.
'''
# Channel types that CivvieBot is willing to track games in.
VALID_CHANNEL_TYPES = [ChannelType.text, ChannelType.public_thread, ChannelType.private_thread]

intents = Intents.default()
intents.members = True # pylint: disable=assigning-non-slot

civviebot = Bot(
    command_prefix=when_mentioned_or("!"),
    description=DESCRIPTION,
    intents=intents,
    allowed_mentions=AllowedMentions(
        everyone=False,
        users=True,
        roles=False),
    debug_guilds=config.DEBUG_GUILDS)

civviebot.load_extension("bot.cogs.base")
civviebot.load_extension("bot.cogs.cleanup")
civviebot.load_extension("bot.cogs.game")
civviebot.load_extension("bot.cogs.notify")
civviebot.load_extension("bot.cogs.player")
civviebot.load_extension("bot.cogs.self")
civviebot.load_extension("bot.cogs.webhookurl")

def purge_channel(channel: int):
    '''
    Cascade deletes the data for a channel.
    '''
    with get_session() as session:
        slug = session.scalar(
            select(WebhookURL.slug).where(WebhookURL.channelid == channel))
        if not slug:
            # Already removed.
            return
        for model in (PlayerGames, TurnNotification, Player, Game, WebhookURL):
            session.execute(delete(model)
                .where(model.slug == slug))
        session.commit()

@civviebot.event
async def on_guild_remove(guild: Guild):
    '''
    Purge everything from the database pertaining to this guild.
    '''
    for channel in guild.channels:
        purge_channel(channel.id)
    logger.info(('CivvieBot was removed from guild %d; any attached webhook URL was removed, and '
        'any attached games and players, were flagged to be removed.'),
        guild.id)

@civviebot.event
async def on_guild_channel_delete(channel: GuildChannel):
    '''
    Removes the associated webhook URL when a channel is deleted.
    '''
    purge_channel(channel.id)
    logger.info('Channel %s was deleted; its URL and associated data were removed.', channel.name)

@civviebot.event
async def on_guild_channel_update(before: GuildChannel, after: GuildChannel):
    '''
    Removes the associated webhook URL if CivvieBot no longer has permission.
    '''
    del before
    try:
        bot_member = get(after.guild.members, id=civviebot.user.id)
        if not after.permissions_for(bot_member).view_channel:
            purge_channel(after.id)
            logger.info(
                ('CivvieBot no longer has permission to view channel %s (guild: %s); its URL and '
                'associated data were removed.'),
                after.name,
                after.guild.name)
    except NotFound:
        purge_channel(after.id)
        logger.info(
            ('Failed to find CivvieBot on an update of channel %s (guild: %s); its URL and '
            'associated data were removed.'),
            after.name,
            after.guild.name)

@civviebot.event
async def on_ready():
    '''
    Logs that the bot is ready.
    '''
    logger.info('%s ready (ID: %d)', civviebot.user, civviebot.user.id)
    if civviebot.debug_guilds:
        logger.info(
            'CivvieBot is running with set debug_guilds. Global commands will not be created.')

@civviebot.event
async def on_application_command(ctx: ApplicationContext):
    '''
    Command reaction for debugging.
    '''
    logger.info(
        '/%s called by %s in %d',
        ctx.command.qualified_name,
        get_display_name(ctx.user),
        ctx.channel_id)
    logger.debug(str(ctx.interaction.data))

@civviebot.event
async def on_application_command_error(ctx: ApplicationContext, error: Exception):
    '''
    Responds to an error invoking a command.
    '''
    if isinstance(error.__context__, (NotFound, command_errors.UserNotFound)):
        await ctx.respond(
            "Sorry, I couldn't find a user by that name; please try again.",
            ephemeral=True)
        return
    if isinstance(error.__context__, NoResultFound):
        await ctx.respond(
            "Sorry, I couldn't find what you were looking for; please try again",
            ephemeral=True)
        return
    await ctx.respond(
        'Sorry, something went wrong trying to run the command; please try again',
        ephemeral=True)
    logger.error('A command encountered an error (initiated by %s in %s): %s\n%s\n%s',
        get_display_name(ctx.user),
        ctx.channel_id,
        error,
        ''.join(format_list(extract_tb(error.__traceback__))),
        'Thrown from previous error:\n' + ''.join(
            format_list(extract_tb(error.__context__.__traceback__))) if error.__context__ else '')

@civviebot.event
async def on_resumed():
    '''
    Logs that a session was resumed.
    '''
    logger.info('CivvieBot session resumed.')
