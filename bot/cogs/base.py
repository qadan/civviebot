'''
Base commands (mostly for providing users documentation).
'''

import logging
from discord import ApplicationContext
from discord.commands import SlashCommandGroup, option
from discord.ext.commands import Cog, Bot
from bot.messaging.base import get_markdown_embed, get_command_list
from utils import config
from utils.utils import get_discriminated_name


NAME = config.get('command_prefix')
DESCRIPTION = 'Get documentation about CivvieBot.'


class BaseCommands(Cog, name=NAME, description=DESCRIPTION):
    '''
    Base commands, not associated with a specific piece of functionality.
    '''

    def __init__(self, bot):
        '''
        Initialization; sets the bot.
        '''
        self.bot: Bot = bot


    base = SlashCommandGroup(NAME, DESCRIPTION)


    @base.command(description="Get a description of how CivvieBot works and how to use it.")
    @option(
        'private',
        type=bool,
        description='Make the response visible only to you',
        default=False)
    async def howto(self, ctx: ApplicationContext, private: bool):
        '''
        Responds with a full how-to embed.
        '''
        await ctx.respond(
            embed=get_markdown_embed(title='How to use CivvieBot', mdfile='howto'),
            ephemeral=private)
        logging.info('"howto" documentation requested by %s (channel: %s)',
            get_discriminated_name(ctx.user),
            ctx.channel_id)


    @base.command(description="Get quick setup instructions for using a game with CivvieBot.")
    @option(
        'private',
        type=bool,
        description='Make the response visible only to you',
        default=False)
    async def quickstart(self, ctx: ApplicationContext, private: bool):
        '''
        Responds with a small quickstart guide embed.
        '''
        await ctx.respond(
            embed=get_markdown_embed(title='Quickstart guide', mdfile='quickstart'),
            ephemeral=private)
        logging.info('"quickstart" documentation requested by %s (channel: %s)',
            get_discriminated_name(ctx.user),
            ctx.channel_id)


    @base.command(description="List all of CivvieBot's commands.")
    @option(
        'private',
        type=bool,
        description='Make the response visible only to you',
        default=False)
    async def commands(self, ctx: ApplicationContext, private: bool):
        '''
        Responds with an embed listing CivvieBot commands.
        '''
        await ctx.respond(
            embed=get_command_list(self.bot),
            ephemeral=private)
        logging.info('"commands" documentation requested by %s (channel: %s)',
            get_discriminated_name(ctx.user),
            ctx.channel_id)


def setup(bot: Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(BaseCommands(bot))
