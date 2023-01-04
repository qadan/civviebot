'''
Messaging components related to players and users.
'''

from time import time
from discord import User, Embed
from discord.ui import View
from discord.ext.commands import Bot
from pony.orm import db_session, left_join
from bot.interactions.player import SelectGameForLinkedPlayers, UnlinkPlayerSelect
from database.models import Game
from utils.utils import expand_seconds_to_string, get_discriminated_name

def get_player_unlink_view(channel_id: int, bot: Bot, target_user: User = None) -> View:
    '''
    Attempts to get the view to unlink players from users.
    '''
    return View(SelectGameForLinkedPlayers(
        UnlinkPlayerSelect(
            channel_id,
            bot,
            target_user=target_user),
        channel_id,
        bot,
        target_user=target_user))

def get_player_upin_embed(channel_id: int, user: User) -> Embed:
    '''
    Gets an embed with the list of Games the given user is up in in a channel.
    '''
    with db_session():
        games = left_join(g for g in Game for p in g.players if
            g.webhookurl.channelid == channel_id and
            g.lastup == p and
            p.discordid == user.id)
        if not games:
            return None
        game_list = Embed(
            title=(f'Games {get_discriminated_name(user)} is up in:'))
        game_list.description = '\n'.join([(f'{game.gamename} (turn {game.turn} - '
            f'{expand_seconds_to_string(time() - game.lastturn)} ago)') for game in games])
        return game_list
