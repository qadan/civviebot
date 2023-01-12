'''
Models for types of entities in CivvieBot's database.

Turn notifications from Civilization 6 contain no uniquely identifying information. The goal of
these models (besides stashing config) is to allow turn notifications to be stashed with a unique
game and player by linking them back to the webhook URL they came from, and to make it easy to ask
about a game's current turn.
'''

from datetime import datetime
from hashlib import sha1
from time import time
from typing import List
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Boolean,
    ForeignKey,
    Table,
    Column,
    desc)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from utils import config

# Maintains a many-to-many relationship between the Player and Game tables.
player_games = Table(
    'player_games',
    DeclarativeBase.metadata,
    Column('playername', ForeignKey('player.name'), primary_key=True),
    Column('gamename', ForeignKey('game.name'), primary_key=True),
    Column('slug', ForeignKey('webhook_url.slug'), primary_key=True))

class WebhookURL(DeclarativeBase): # pylint: disable=too-few-public-methods
    '''
    Represents a URL the API can receive turn notifications at.
    '''
    __tablename__ = 'webhook_url'

    @staticmethod
    def generate_slug():
        '''
        Generates a slug to make a webhook URL.
        '''
        hasher = sha1(str(time()).encode('UTF-8'))
        return hasher.hexdigest()[:16]

    # Unique 16 character hashed hex code.
    slug: Mapped[str] = mapped_column(String(16), primary_key=True, default_factory=generate_slug())
    # The snowflake of the channel this URL operates in.
    channelid: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    # Configurable minimum turns, which games then inherit.
    limitwarned: Mapped[bool] = mapped_column(Boolean, default=None)
    # One-to-many relationship to the Game table.
    games: Mapped[List['Game']] = relationship(
        'Game',
        back_populates='webhookurl',
        cascade='save-update, merge, delete')

class TurnNotification(DeclarativeBase): # pylint: disable=too-few-public-methods
    '''
    Represents a stashed Civilization 6 turn notification.
    '''
    __tablename__ = 'turn_notification'
    # The turn number reported by this notification.
    turn: Mapped[int] = mapped_column(Integer, primary_key=True)
    # The name of the player reported by this notification.
    playername: Mapped[str] = mapped_column(ForeignKey('player.name'), primary_key=True)
    # The name of the game reported by this notification.
    gamename: Mapped[str] = mapped_column(ForeignKey('game.name'), primary_key=True)
    # The slug of the URL this notification was POSTed to.
    slug: Mapped[str] = mapped_column(ForeignKey('webhook_url.slug'), primary_key=True)
    # The time this notification came in.
    logtime: Mapped[datetime] = mapped_column(DateTime, required=True)
    # The last time this notification was pinged in Discord (None for never).
    lastnotified: Mapped[datetime] = mapped_column(DateTime, default=None)
    # One-to-one relationship to the Player table.
    player: Mapped['Player'] = relationship(back_populates='turns', lazy='immediate')
    # One-to-many relationship to the Game table.
    game: Mapped['Game'] = relationship(back_populates='turns', lazy='immediate')

class Game(DeclarativeBase): # pylint: disable=too-few-public-methods
    '''
    Represents a game being tracked from Civilization 6.
    '''
    __tablename__ = 'game'
    # The registered name of this game.
    name: Mapped[str] = mapped_column(String, primary_key=True)
    # The slug of the webhook URL this game is registered to.
    slug: Mapped[str] = mapped_column(ForeignKey('webhook_url.slug'), primary_key=True)
    # Whether we should pop notifications for this game at all.
    muted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Whether we have warned about detecting a duplicate game. If null, we do
    # not know of a duplicate we need to warn about.
    duplicatewarned: Mapped[bool] = mapped_column(Boolean, default=None)
    # How frequently turn reminders pop for this game. If null, reminders are not sent.
    remindinterval: Mapped[int] = mapped_column(Integer, default=config.REMIND_INTERVAL)
    # Notifications and reminders will not pop for a game whose current turn is under this number.
    minturns: Mapped[int] = mapped_column(Integer, nullable=False, default=config.MIN_TURNS)
    # One-to-one relationship to the WebhookURL table.
    webhookurl: Mapped[WebhookURL] = relationship(
        'WebhookURL',
        back_populates='games',
        lazy='immediate')
    # Many-to-many relationship to the Player table via the player_games table.
    players: Mapped[List['Player']] = relationship(
        'Player',
        back_populates='games',
        secondary=player_games,
        cascade='save-update, merge, delete')
    # One-to-many relationship to the TurnNotification table.
    turns: Mapped[List[TurnNotification]] = relationship(
        back_populates='game',
        order_by=desc(TurnNotification.logtime))

class Player(DeclarativeBase): # pylint: disable=too-few-public-methods
    '''
    Represents a player being tracked in a Civilization 6 game.
    '''
    __tablename__ = 'player'
    # The name of this player, obtained from Civilization 6.
    name: Mapped[str] = mapped_column(String, primary_key=True)
    # The slug of the URL this player was obtained from.
    slug: Mapped[str] = mapped_column(ForeignKey('webhook_url.slug'), primary_key=True)
    # The snowflake of the Discord user this player is linked to.
    discordid: Mapped[int] = mapped_column(Integer, default=None)
    # Many-to-many relationship to the Game table via the player_games table.
    games: Mapped[List[Game]] = relationship(
        back_populates='players',
        secondary=player_games,
        cascade='save-update, merge, delete')
    # Reference relationship to the WebhookURL tracking this player.
    webhookurl: Mapped[WebhookURL] = relationship(viewonly=True)
