'''
Builders for different parts of messages sent about games.
'''

from discord import Embed
from discord.commands import ApplicationContext
from discord.ext.commands import Bot
from pony.orm import db_session
from bot.cogs.base import NAME as BASE_NAME
from bot.cogs.player import NAME as PLAYER_NAME
from database.models import Game, Player
from utils import config
from utils.utils import generate_url, expand_seconds_to_string, get_discriminated_name


def get_game_info_embed(game_id: int, bot: Bot):
    '''
    Gets the embed to use when generating a game info message.
    '''
    with db_session():
        game = Game[game_id]
        if not game:
            embed = Embed(title='Missing game')
            embed.description=('Failed to find the given game; was it deleted before information '
                'could be provided?')
            return embed
        embed = Embed(title=f'Information and settings for {game.gamename}')
        embed.add_field(name='Current turn:', value=game.turn, inline=True)
        embed.add_field(name='Current player:', value=game.lastup.playername, inline=True)
        embed.add_field(name='Most recent turn:', value=f'<t:{int(game.lastturn)}:R>', inline=True)
        embed.add_field(
            name='Re-ping frequency:',
            value=expand_seconds_to_string(game.notifyinterval),
            inline=True)
        embed.add_field(name='Notifies after:', value=f'Turn {game.minturns}', inline=True)
        embed.add_field(name='Is muted:', value='Yes' if game.muted else 'No')

        def player_to_string(player: Player):
            if player.discordid:
                user = bot.get_user(int(player.discordid))
                if not user:
                    return (f'{player.playername} (linked to a Discord user that could not be '
                        f'found and may no longer be in this channel; use /{PLAYER_NAME} unlink if '
                        'this should be cleaned up)')
                return f'{player.playername} (linked to {get_discriminated_name(user)})'
            return f'{player.playername} (no linked Discord user)'
        embed.add_field(
            name='Known players:',
            value='\n'.join([player_to_string(player) for player in game.players]),
            inline=False)

        embed.add_field(name='Webhook URL:', value=generate_url(game.webhookurl.slug))
        command_prefix = config.get('command_prefix')
    embed.set_footer(text=('If you\'re part of this game, place the above webhook URL in your '
        'Civilization 6 settings to send notifications to CivvieBot when you take your turn (use '
        f'"/{command_prefix} quickstart" for more setup information).'))
    return embed


@db_session
def get_game_list_embed(ctx: ApplicationContext):
    '''
    Gets the embed to use when generating a message listing all games in a channel.
    '''
    embed = Embed(title='All active games in this channel:')
    games = Game.select(lambda g: g.webhookurl.channelid == str(ctx.channel_id))
    if games:
        game_list = [f'{game.gamename} ({generate_url(game.webhookurl.slug)})' for game in games]
        embed.add_field(name='Games:', value='\n'.join(game_list))
        embed.set_footer(text='To get information about a specific game, use "/c6game info".')
    else:
        embed.description = ('There are no active games in this channel. For setup instructions '
            f'use `/{BASE_NAME} quickstart` for a quick setup guide, or `/{BASE_NAME} howto` for '
            'an overview of CivvieBot.')
    return embed


def get_game_edit_response_embed(game: Game):
    '''
    Gets a response embed appropriate for a newly-edited Game.
    '''
    response_embed = Embed()
    response_embed.add_field(
        name='Stale notification interval:',
        value=expand_seconds_to_string(game.notifyinterval))
    response_embed.add_field(
        name='Minimum turns before pinging:',
        value=game.minturns)
