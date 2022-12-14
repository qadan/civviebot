'''
Builders for portions of messages dealing with users.
'''

from discord import Embed, User
from database.models import Game


def get_user_game_list_embed(games: Game, user: User):
    '''
    Gets the embed that should be used when showing the list of games a user's players are in.
    '''
    game_list = Embed(
        title=f'Games {user.display_name} is part of in this channel:'
    )
    game_list.add_field(name='Games', value='\n'.join([game.gamename for game in games]))
    return game_list


def get_user_game_upin_list_embed(games: Game, user: User):
    '''
    Gets the embed that should be used when showing the list of games a user's players are up in.
    '''
    game_list = Embed(
        title=f'Games {user.display_name} is part of in this channel and is currently up in:'
    )
    game_list.add_field(name='Games', value='\n'.join([game.gamename for game in games]))
    return game_list
