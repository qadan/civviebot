'''
Base commands (mostly for providing users documentation).
'''

import logging
from os import path
from discord import ApplicationContext, Embed
from discord.commands import SlashCommandGroup, option
from discord.ext.commands import Cog, Bot
from bot.interactions import base as base_interactions
from bot.interactions.common import View
from utils import config, permissions
from utils.utils import get_discriminated_name

logger = logging.getLogger(f'civviebot.{__name__}')

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
    base.default_member_permissions = permissions.base_level

    @base.command(description="Get information about how CivvieBot works and how to use it.")
    @option(
        'private',
        type=bool,
        description='Make the response visible only to you',
        default=True)
    async def faq(self, ctx: ApplicationContext, private: bool):
        '''
        Responds with a full how-to embed.
        '''
        await ctx.respond(
            'What would you like to know more about?',
            view=View(base_interactions.FaqQuestionSelect()),
            ephemeral=private)

    @base.command(description="Get setup instructions for using a game with CivvieBot.")
    @option(
        'private',
        type=bool,
        description='Make the response visible only to you',
        default=False)
    async def quickstart(self, ctx: ApplicationContext, private: bool):
        '''
        Responds with a small quickstart guide embed.
        '''
        embed = Embed(title='Quickstart guide')
        with open(
            path.join(
                path.dirname(path.realpath(__file__)),
                'markdown',
                'quickstart.md'),
            'r',
            encoding='UTF-8') as description:
            embed.description = description.read().replace(
                '%COMMAND_PREFIX%',
                config.get('command_prefix'))
        await ctx.respond(embed=embed, ephemeral=private)
        logger.info('"quickstart" documentation requested by %s (channel: %s)',
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
        embed = Embed(title='CivvieBot commands:')
        description = ''
        for cog in self.bot.cogs.values():
            if cog.qualified_name[:2] == 'c6':
                description += f'__**{cog.qualified_name}**__\n{cog.description}\n\n'
                for command in cog.walk_commands():
                    if command.name:
                        command_desc = getattr(command, 'description', None)
                        if command_desc:
                            description += f'`/{command.qualified_name}`: {command_desc}\n'
                description += '\n'
        embed.description = description
        await ctx.respond(
            embed=embed,
            ephemeral=private)
        logger.info('"commands" documentation requested by %s (channel: %s)',
            get_discriminated_name(ctx.user),
            ctx.channel_id)

def setup(bot: Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(BaseCommands(bot))
