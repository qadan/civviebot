'''
Messaging components related to players and users.
'''

from datetime import datetime
from typing import List
from discord import User, Embed
from sqlalchemy import select, func
from database.models import TurnNotification, Player, Game
from database.utils import get_session
from utils.utils import expand_seconds_to_string, get_discriminated_name

def get_player_upin_embed(channel_id: int, user: User) -> Embed:
    '''
    Gets an embed with the list of Games the given user is up in in a channel.
    '''
    with get_session() as session:
        turns: List[TurnNotification] = session.scalars(select(TurnNotification).where(
            func.max(TurnNotification.logtime)
            and TurnNotification.player.discordid == user.id
            and TurnNotification.game.channelid == channel_id)).all()
        if not turns:
            return None
        game_list = Embed(title=(f'Games {get_discriminated_name(user)} is up in:'))
        game_list.description = '\n'.join([(f'{turn.game.name} (turn {turn.turn} - '
            f'{expand_seconds_to_string((datetime.now() - turn.logtime).total_seconds())} ago)')
            for turn in turns])
        return game_list

def get_player_games_embed(channel_id: int, user: User) -> Embed:
    '''
    Gets an embed with the list of Games the given user is in in a channel.
    '''
    with get_session() as session:
        game_list = Embed()
        games = session.scalars(select(Game).join(Player, Player.slug == Game.slug).where(
            Player.discordid == user.id
            and Player.webhookurl.channelid == channel_id)).all()
        if games:
            game_list.description = '\n'.join([game.name for game in games])
        else:
            game_list.description = ('You do not appear to be linked to any players in any active '
                'games in this channel.')
        return game_list
