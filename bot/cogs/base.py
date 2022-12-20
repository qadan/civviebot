'''
Base commands (mostly for providing users documentation).
'''

import logging
from os import path
from discord import ApplicationContext, Embed
from discord.commands import SlashCommandGroup, option
from discord.ext.commands import Cog, Bot
from utils import config
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


    @staticmethod
    def get_markdown_embed(title: str, mdfile: str) -> Embed:
        '''
        Gets an embed with a given title, the contents of which are parsed from mdfile.

        The mdfile should be relative to ./markdown. Replaces %COMMAND_PREFIX% in the markdown with
        the actual configured command prefix.
        '''
        embed = Embed(title=title)
        with open(
            path.join(
                path.dirname(path.realpath(__file__)),
                'markdown',
                f'{mdfile}.md'),
            'r',
            encoding='UTF-8') as description:
            embed.description = description.read().replace(
                '%COMMAND_PREFIX%',
                config.get('command_prefix'))
        return embed


    @base.command(description="Get a description of how CivvieBot works and how to use it.")
    @option(
        'private',
        type=bool,
        description='Make the response visible only to you',
        default=False)
    async def faq(self, ctx: ApplicationContext, private: bool):
        '''
        Responds with a full how-to embed.
        '''
        await ctx.respond(
            embed=self.get_markdown_embed('Frequently Asked Questions', 'faq'),
            ephemeral=private)
        logger.info('"faq" documentation requested by %s (channel: %s)',
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
            embed=self.get_markdown_embed('Quickstart guide', 'quickstart'),
            ephemeral=private)
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
