'''
Utility functions for the database.
'''

from sqlalchemy import select, delete, Subquery, func
from sqlalchemy.exc import IntegrityError
from .connect import get_db, get_session
from .models import WebhookURL, Game, Player, TurnNotification, PlayerGames


def emit_all():
    '''
    Emits all DDL statements to the database.
    '''
    database = get_db()
    WebhookURL.metadata.create_all(database)
    Game.metadata.create_all(database)
    Player.metadata.create_all(database)
    PlayerGames.metadata.create_all(database)
    TurnNotification.metadata.create_all(database)


def get_url_for_channel(channel_id: int) -> WebhookURL:
    '''
    Gets the URL for a channel, creating it if it doesn't exist.
    '''
    with get_session() as session:
        url = session.scalar(
            select(WebhookURL)
            .where(WebhookURL.channelid == channel_id)
        )
        if not url:
            try:
                url = WebhookURL(channelid=channel_id)
                session.add(url)
                session.commit()
            except IntegrityError:
                session.rollback()
                url = session.scalar(
                    select(WebhookURL)
                    .where(WebhookURL.channelid == channel_id)
                )
    return url


def delete_game(game: int, channel_id: int):
    '''
    Deletes a game and associated notifications and links from a channel.
    '''
    with get_session() as session:
        slug = session.scalar(
            select(WebhookURL.slug)
            .where(WebhookURL.channelid == channel_id)
        )
        session.execute(
            delete(TurnNotification)
            .where(TurnNotification.gameid == game)
            .where(TurnNotification.slug == slug)
        )
        session.execute(
            delete(PlayerGames)
            .where(PlayerGames.gameid == game)
            .where(PlayerGames.slug == slug)
        )
        session.execute(
            delete(Game)
            .where(Game.id == game)
            .where(Game.slug == slug)
        )
        session.commit()


def date_rank_subquery(channel_id: int = None) -> Subquery:
    '''
    Gets a Subquery, potentially filtered by channel_id, that ranks
    TurnNotifications by logtime (descending) and partitions by unique games
    per unique slug.

    The rank is attached to the subquery as 'date_rank', where 1 is the most
    recent turn notification for its game.
    '''
    subquery = (
        select(
            func.rank().over(
                order_by=TurnNotification.logtime.desc(),
                partition_by=TurnNotification.gameid
            ).label('date_rank'),
            TurnNotification.turn,
            TurnNotification.playerid,
            TurnNotification.gameid,
            TurnNotification.slug,
            TurnNotification.logtime,
            TurnNotification.lastnotified
        )
        .select_from(TurnNotification)
    )
    if channel_id:
        subquery = (
            subquery.join(TurnNotification.webhookurl)
            .where(WebhookURL.channelid == channel_id)
        )
    return subquery.subquery()
