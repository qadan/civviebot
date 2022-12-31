'''
CivvieBot cog to handle commands dealing with Webhook URLs.
'''

from discord import ApplicationContext, Embed
from discord.commands import SlashCommandGroup, option
from discord.ext.commands import Cog, Bot
from pony.orm import db_session
from database.models import WebhookURL
from bot.interactions.common import View
import bot.interactions.webhookurl as whurl_interactions
from utils import config, permissions
from utils.errors import ValueAccessError
from utils.utils import VALID_CHANNEL_TYPES, generate_url, pluralize

NAME = config.get('command_prefix') + 'url'
DESCRIPTION = 'Create and manage webhook URLs in this channel.'
NO_URLS_FOUND = ("I couldn't find any URLs that track games in this channel. To create a new URL, "
    f'use `/{NAME} new`.')

class WebhookURLCommands(Cog, name=NAME, description=DESCRIPTION):
    '''
    Command group for creating, modifying, removing, and getting information about Webhook URLs.
    '''

    def __init__(self, bot):
        '''
        Initialization; sets the bot.
        '''
        self.bot: Bot = bot

    urls = SlashCommandGroup(NAME, 'Get information about URLs that track games in this channel.')
    urls.default_member_permissions = permissions.base_level
    url_manage = SlashCommandGroup(NAME + '_manage', DESCRIPTION)
    url_manage.default_member_permissions = permissions.admin_level

    @url_manage.command(description='Generates a new Civilization 6 webhook URL')
    async def new(self, ctx: ApplicationContext):
        '''
        Creates a new Civilization 6 webhook URL.
        '''
        await ctx.send_modal(
            whurl_interactions.NewWebhookModal(
                ctx.channel_id,
                ctx.bot,
                title='New Webhook URL'))

    @url_manage.command(
        description="Updates a URL with the given information. Only affects future games")
    async def edit(self, ctx: ApplicationContext):
        '''
        Updates a webhook URL in the database with a given set of information.
        '''
        try:
            await ctx.respond(
                'Select a webhook URL to edit:',
                view=View(whurl_interactions.SelectUrlForEdit(ctx.channel_id, ctx.bot)),
                ephemeral=True)
        except ValueAccessError:
            await ctx.respond(NO_URLS_FOUND, ephemeral=True)

    @url_manage.command(description="Move a webhook URL to a different channel")
    async def move(self, ctx: ApplicationContext):
        '''
        Modifies the channelid of a webhook URL with a given new channel.
        '''
        try:
            await ctx.respond(
                'Select a webhook URL to move:',
                view=View(whurl_interactions.SelectUrlForMove(ctx.channel_id, ctx.bot)),
                ephemeral=True)
        except ValueAccessError:
            await ctx.respond(NO_URLS_FOUND, ephemeral=True)

    @url_manage.command(
        description='Deletes a URL so it can no longer receive updates. Removes associated games.')
    async def delete(self, ctx: ApplicationContext):
        '''
        Deletes a webhook URL from the database.
        '''
        try:
            await ctx.respond(
                'Select a webhook URL to delete:',
                view=View(whurl_interactions.SelectUrlForDelete(ctx.channel_id, ctx.bot)),
                ephemeral=True)
        except ValueAccessError:
            await ctx.respond(NO_URLS_FOUND, ephemeral=True)

    @urls.command(description='Prints out info about a URL')
    @option(
        'private',
        type=bool,
        description='Make the response visible only to you',
        default=True)
    async def info(self, ctx: ApplicationContext, private: bool):
        '''
        Responds with an embed containing webhook URL information.
        '''
        try:
            await ctx.respond(
                'Select a webhook URL to get info about:',
                view=View(whurl_interactions.SelectUrlForInfo(ctx.channel_id, ctx.bot)),
                ephemeral=private)
        except ValueAccessError:
            await ctx.respond(NO_URLS_FOUND, ephemeral=private)

    @urls.command(description='List all webhook URLs created in this channel')
    @option(
        'private',
        type=bool,
        description='Make the response visible only to you',
        default=True)
    @option(
        'list_all',
        type=bool,
        description='List all URLs in this server, not just this channel',
        default=False)
    async def list(self, ctx: ApplicationContext, private: bool, list_all: bool):
        '''
        Responds with an embed containing a list of all URLs associated with this channel.
        '''
        with db_session():
            if list_all:
                channels = [str(channel.id) for channel
                    in self.bot.get_channel(ctx.channel_id).guild.channels
                    if channel.type in VALID_CHANNEL_TYPES]
                urls = WebhookURL.select(lambda whu: whu.channelid in channels)
                whurl_list = Embed(title='All webhook URLs in this server:')
                def urlstring(url: WebhookURL):
                    return (f'{generate_url(url.slug)} ({pluralize("game", url.games)}, in '
                        f'<#{url.channelid}>)')
            else:
                urls = WebhookURL.select(lambda whu: whu.channelid == ctx.channel_id)
                whurl_list = Embed(title='All webhook URLs in this channel:')
                def urlstring(url: WebhookURL):
                    return f'{generate_url(url.slug)} ({pluralize("game", url.games)})'
            if not urls:
                scope = 'server' if list_all else 'channel'
                whurl_list.description = (f'There are no webhook URLs created in this {scope}. Use '
                    f'`/{NAME} new` to get one started.')
            else:
                urls = '\n'.join([urlstring(url) for url in urls])
                whurl_list.add_field(name='URLs:', value=urls)
                whurl_list.set_footer(
                    text=(f'To get a list of all active games attached to a URL, use "/{NAME} '
                        'info" to select the URL you would like information about.'))
        await ctx.respond(embed=whurl_list, ephemeral=private)

def setup(bot: Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(WebhookURLCommands(bot))
