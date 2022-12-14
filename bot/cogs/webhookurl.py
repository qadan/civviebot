'''
CivvieBot cog to handle commands dealing with Webhook URLs.
'''

from discord import ApplicationContext
from discord.commands import SlashCommandGroup, option
from discord.ui import View
from discord.ext.commands import Cog, Bot
from pony.orm import db_session
from database.models import WebhookURL
import bot.interactions.webhookurl as whurl_interactions
import bot.messaging.webhookurl as whurl_messaging
from utils import config


NAME = config.get('command_prefix') + 'url'
DESCRIPTION = 'Create and manage webhook URLs in this channel.'


class WebhookURLCommands(Cog, name=NAME, description=DESCRIPTION):
    '''
    Command group for creating, modifying, removing, and getting information about Webhook URLs.
    '''

    def __init__(self, bot):
        '''
        Initialization; sets the bot.
        '''
        self.bot: Bot = bot
    urls = SlashCommandGroup(NAME, DESCRIPTION)


    @urls.command(description='Generates a new Civilization 6 webhook URL')
    async def new(self, ctx: ApplicationContext):
        '''
        Creates a new Civilization 6 webhook URL.
        '''
        await ctx.send_modal(
            whurl_interactions.NewWebhookModal(
                title='New Webhook URL',
                channel_id=ctx.channel_id,
                bot=ctx.bot))


    @urls.command(description="Updates a URL with the given information. Only affects future games")
    async def edit(self, ctx: ApplicationContext):
        '''
        Updates a webhook URL in the database with a given set of information.
        '''
        await ctx.respond(
            'Select a webhook URL to edit:',
            view=View(
                whurl_interactions.SelectUrlForEdit(
                    channel_id=ctx.channel_id,
                    bot=ctx.bot)),
            ephemeral=True)


    @urls.command(
        description='Deletes a URL so it can no longer receive updates. Removes associated games.')
    async def delete(self, ctx: ApplicationContext):
        '''
        Deletes a webhook URL from the database.
        '''
        await ctx.respond(
            'Select a webhook URL to delete:',
            view=View(
                whurl_interactions.SelectUrlForDelete(
                    channel_id=ctx.channel_id,
                    bot=ctx.bot)),
            ephemeral=True)


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
        await ctx.respond(
            'Select a webhook URL to get info about:',
            view=View(
                whurl_interactions.SelectUrlForInfo(
                    channel_id=ctx.channel_id,
                    bot=ctx.bot,
                    private=private)))


    @urls.command(description='List all webhook URLs created in this channel')
    @option(
        'private',
        type=bool,
        description='Make the response visible only to you',
        default=True)
    async def list(self, ctx: ApplicationContext, private: bool):
        '''
        Responds with an embed containing a list of all URLs associated with this channel.
        '''
        with db_session():
            urls = WebhookURL.select(lambda whu: whu.channelid == ctx.interaction.channel_id)
            await ctx.respond(embed=whurl_messaging.get_list_embed(urls), ephemeral=private)


def setup(bot: Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(WebhookURLCommands(bot))
