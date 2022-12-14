'''
Builders for different parts of messages sent about CivvieBot.
'''

from os import path
from discord import Embed
from discord.ext.commands import Bot
from utils import config


MD_FOLDER = path.join(path.dirname(path.realpath(__file__)), 'markdown')[:]


def get_markdown_embed(title: str, mdfile: str):
    '''
    Gets an embed with a given title, the contents of which are parsed from mdfile.

    The mdfile should be relative to ./markdown. Replaces %COMMAND_PREFIX% in the markdown with the
    actual configured command prefix.
    '''
    embed = Embed(title=title)
    with open(path.join(MD_FOLDER, f'{mdfile}.md'), 'r', encoding='UTF-8') as description:
        embed.description = description.read().replace(
            '%COMMAND_PREFIX%',
            config.get('command_prefix'))
    return embed


def get_command_list(bot: Bot):
    '''
    Gets an embed with a list of all commands supported by CivvieBot.
    '''
    embed = Embed(title='CivvieBot commands:')
    description = ''
    for cog in bot.cogs.values():
        if cog.qualified_name[:2] == 'c6':
            description += f'__**{cog.qualified_name}**__\n{cog.description}\n\n'
        for command in cog.walk_commands():
            if command.name:
                command_desc = getattr(command, 'description', None)
                if command_desc:
                    description += f'`/{command.qualified_name}`: {command_desc}\n'
        description += '\n'
    embed.description = description
    return embed
