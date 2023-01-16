'''
Builders for portions of messages dealing with games.
'''

from datetime import datetime, timedelta
from discord import Embed
from discord.ext.commands import Bot
from sqlalchemy import select, func
from database.models import Game, TurnNotification, WebhookURL
from database.connect import get_session
from utils import config
from utils.string import expand_seconds, get_display_name


CLEANUP_CONTENT = 'Information about the game cleanup schedule:'


async def get_info_embed(game: Game, bot: Bot) -> Embed:
    '''
    Gets the embed to provide info about a game.
    '''
    with get_session() as session:
        session.add(game)
        embed = Embed(title=game.name)
        if not game.turns:
            embed.add_field(
                name='Current turn:',
                value='No turns have been tracked yet for this game.'
            )
        else:
            embed.add_field(
                name='Current turn:',
                value=game.turns[0].turn,
                inline=True
            )
            current_player = (
                await bot.fetch_user(game.turns[0].player.discordid)
                if game.turns[0].player.discordid
                else None
            )
            embed.add_field(
                name='Current player:',
                value=(
                    (f'{game.turns[0].player.name} ('
                     '{get_display_name(current_player)})')
                    if current_player
                    else game.turns[0].player.name
                ),
                inline=True)
            embed.add_field(
                name='Most recent turn:',
                value=f'<t:{int(game.turns[0].logtime.timestamp())}:R>',
                inline=True
            )
            if (
                game.remindinterval
                and game.turns[0].lastnotified
                and game.turns[0].turn > game.minturns
                and not game.muted
            ):
                embed.add_field(
                    name='Next reminder:',
                    value=(f'<t:{int(game.nextremind.timestamp())}:R>'),
                    inline=True
                )
        embed.add_field(
            name='Notifies after:',
            value=f'Turn {game.minturns}',
            inline=True
        )
        embed.add_field(
            name='Is muted:',
            value='Yes' if game.muted else 'No',
            inline=True
        )
        embed.add_field(
            name='Tracked players:',
            value=len(game.players),
            inline=True
        )
        embed.add_field(name='Webhook URL:', value=game.full_url)
    embed.set_footer(
        text=(
            'If you\'re part of this game, place the above webhook URL in '
            'your Civilization 6 settings to send notifications to CivvieBot '
            f'when you take your turn use "/{config.COMMAND_PREFIX} '
            'quickstart" for more setup information). For a list of known '
            f'players use "/{config.COMMAND_PREFIX}game players".'
        )
    )
    return embed


def get_cleanup_embed(channel: int) -> Embed:
    '''
    Gets the embed for displaying cleanup information.
    '''
    embed = Embed(title='Cleanup schedule and statistics:')
    embed.description = (
        'During cleanup, games that are considered "stale" are deleted. When '
        'a game is deleted by any means, its players are marked to be '
        'deleted, which also occurs during cleanup.'
    )
    embed.add_field(
        name='A game is considered stale:',
        value=(
            f'{expand_seconds(config.STALE_GAME_LENGTH)} after the last '
            'received notification'
        )
    )
    embed.add_field(
        name='Cleanup occurs every:',
        value=expand_seconds(config.CLEANUP_INTERVAL)
    )
    embed.add_field(
        name='Cleanup removes:',
        value=f'{config.CLEANUP_LIMIT} of each type of record'
    )
    stale_time = datetime.now() - timedelta(seconds=config.STALE_GAME_LENGTH)
    with get_session() as session:
        stale_games = session.scalar(
            select(func.count())
            .select_from(Game)
            .join(Game.webhookurl)
            .join(Game.turns)
            .where(TurnNotification.logtime < stale_time)
            .where(WebhookURL.channelid == channel)
            .distinct()
        )
    embed.add_field(name='Current stale games:', value=stale_games)
    return embed
