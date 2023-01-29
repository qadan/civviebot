'''
Messaging components related to players and users.
'''

from typing import Tuple
from discord import User, Embed
from sqlalchemy import select, Row
from database.connect import get_session
from database.models import Player, Game, WebhookURL
from database.utils import date_rank_subquery
from utils import config
from utils.string import get_display_name


def get_player_upin_embed(channel_id: int, user: User) -> Embed:
    '''
    Gets an embed with the list of Games the given user is up in in a channel.
    '''
    game_list = Embed(title=(f'Games {get_display_name(user)} is up in:'))
    with get_session() as session:
        subquery = date_rank_subquery(channel_id=channel_id)
        turns = session.execute(
            select(
                subquery.c.gameid,
                subquery.c.logtime,
                subquery.c.turn,
                subquery.c.date_rank,
                subquery.c.playerid
            )
            .join(Player, Player.id == subquery.c.playerid)
            .where(Player.discordid == user.id)
            .where(subquery.c.date_rank == 1)
        )
        if turns:
            def to_string(row: Row[Tuple]) -> str:
                return (
                    f'{row.game.name} (turn {row.turn} - '
                    f'<t:{int(row.logtime.timestamp())}:R>)'
                )
            game_list.description = '\n'.join(
                [to_string(turn) for turn in turns]
            )
        else:
            game_list.description = (
                f"**{get_display_name(user)}** doesn't appear to be up in any "
                "games I'm tracking in this channel."
            )
        return game_list


def get_player_games_embed(channel_id: int, user: User) -> Embed:
    '''
    Gets an embed with the list of Games the given user is in in a channel.
    '''
    with get_session() as session:
        game_list = Embed(
            title=(f'Games {get_display_name(user)} is linked to in this '
                   'channel:'))
        games = session.scalars(
            select(Game)
            .join(Game.webhookurl)
            .join(Game.players)
            .where(Player.discordid == user.id)
            .where(WebhookURL.channelid == channel_id)
            .distinct(Game.name)
        )
        if games:
            game_list.description = '\n'.join([game.name for game in games])
            game_list.set_footer(
                text=('For more information about a game, use '
                      f'"/{config.COMMAND_PREFIX}game info".')
            )
        else:
            game_list.description = (
                f"**{get_display_name(user)}** doesn't appear to be linked to "
                "any players in any games I'm tracking in this channel."
            )
        return game_list
