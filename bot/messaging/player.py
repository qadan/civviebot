'''
Messaging components related to players and users.
'''

from discord import User, Embed
from sqlalchemy import select, and_
from sqlalchemy.orm import aliased
from database.models import TurnNotification, Player, Game, WebhookURL
from database.utils import get_session
from utils import config
from utils.utils import get_discriminated_name

def get_player_upin_embed(channel_id: int, user: User) -> Embed:
    '''
    Gets an embed with the list of Games the given user is up in in a channel.
    '''
    game_list = Embed(title=(f'Games {get_discriminated_name(user)} is up in:'))
    with get_session() as session:
        turnnotification_aliased = aliased(TurnNotification)
        turns = session.scalars(select(TurnNotification)
            .join(TurnNotification.game)
            .outerjoin(turnnotification_aliased, and_(
                TurnNotification.gamename == turnnotification_aliased.gamename,
                TurnNotification.playername == turnnotification_aliased.playername,
                TurnNotification.slug == turnnotification_aliased.slug,
                TurnNotification.logtime > turnnotification_aliased.logtime))
            .where(Player.discordid == user.id)
            .where(WebhookURL.channelid == channel_id)).all()
        if turns:
            game_list.description = '\n'.join([(f'{turn.game.name} (turn {turn.turn} - '
                f'<t:{int(turn.logtime.timestamp())}:R>)')
                for turn in turns])
        else:
            game_list.description = ("This user doesn't appear to be up in any games I'm tracking "
                "in this channel.")
        return game_list

def get_player_games_embed(channel_id: int, user: User) -> Embed:
    '''
    Gets an embed with the list of Games the given user is in in a channel.
    '''
    with get_session() as session:
        game_list = Embed(
            title=f'Games {get_discriminated_name(user)} is linked to in this channel:')
        games = session.scalars(select(Game)
            .join(Player, Player.discordid == user.id)
            .join(Player.webhookurl)
            .where(WebhookURL.channelid == channel_id)).all()
        if games:
            game_list.description = '\n'.join([game.name for game in games])
            game_list.set_footer(text=('For more information about a game, use "/'
                f'{config.COMMAND_PREFIX}game info".'))
        else:
            game_list.description = ("This user don't appear to be linked to any players in any "
                "games I'm tracking in this channel.")
        return game_list
