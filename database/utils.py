'''
Connection management functionality and base utilities for the CivvieBot database.
'''

from sqlalchemy import create_engine, URL, Engine, select, delete, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased
from utils import config
from .models import WebhookURL, Game, Player, TurnNotification, PlayerGames

def get_db() -> Engine:
    '''
    Gets an Engine representing the CivvieBot database.
    '''
    url = URL.create(
        f'{config.CIVVIEBOT_DB_DIALECT}+{config.CIVVIEBOT_DB_DRIVER}',
        **config.DB_URL_KWARGS)
    database = create_engine(url)
    return database

def get_session() -> Session:
    '''
    Gets a session for the CivvieBot database.
    '''
    return Session(get_db())

def emit_all():
    '''
    Emits all DDL statements to the database.
    '''
    database = get_db()
    WebhookURL.metadata.create_all(database)
    PlayerGames.metadata.create_all(database)
    Game.metadata.create_all(database)
    Player.metadata.create_all(database)
    TurnNotification.metadata.create_all(database)

def get_url_for_channel(channel_id: int) -> WebhookURL:
    '''
    Gets the URL for a channel, creating it if it doesn't exist.
    '''
    with get_session() as session:
        url = session.scalar(select(WebhookURL).where(WebhookURL.channelid == channel_id))
        if not url:
            try:
                url = WebhookURL(channelid=channel_id)
                session.add(url)
                session.commit()
            except IntegrityError:
                session.rollback()
                url = session.scalar(select(WebhookURL).where(WebhookURL.channelid == channel_id))
    return url

def delete_game(game: str, channel_id: int):
    '''
    Deletes a game and associated notifications and links from a channel.
    '''
    with get_session() as session:
        slug = session.scalar(select(WebhookURL.slug)
            .where(WebhookURL.channelid == channel_id))
        session.execute(delete(TurnNotification)
            .where(TurnNotification.gamename == game)
            .where(TurnNotification.slug == slug))
        session.execute(delete(PlayerGames)
            .where(PlayerGames.gamename == game)
            .where(PlayerGames.slug == slug))
        session.execute(delete(Game)
            .where(Game.name == game)
            .where(Game.slug == slug))
        session.commit()

def aliased_highest_turn_notification():
    '''
    Returns a SELECT statement outer-joined on the highest turn notification.
    '''
    turnnotification_aliased = aliased(TurnNotification)
    return (select(TurnNotification)
        .outerjoin(turnnotification_aliased, and_(
            TurnNotification.gamename == turnnotification_aliased.gamename,
            TurnNotification.playername == turnnotification_aliased.playername,
            TurnNotification.slug == turnnotification_aliased.slug,
            TurnNotification.logtime > turnnotification_aliased.logtime)))
