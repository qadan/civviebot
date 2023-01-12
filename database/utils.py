'''
Connection management functionality and base utilities for the CivvieBot database.
'''

from sqlalchemy import create_engine, URL, Engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
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
            except IntegrityError as error:
                session.rollback()
                url = session.scalar(select(WebhookURL).where(WebhookURL.channelid == channel_id))
    return url
