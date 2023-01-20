'''
Models for types of entities in CivvieBot's database.

Turn notifications from Civilization 6 contain no uniquely identifying
information. The goal of these models (besides stashing config) is to allow
turn notifications to be stashed with a unique game and player by linking them
back to the webhook URL they came from, and to make it easy to ask about a
game's current turn.
'''

from datetime import datetime
from hashlib import sha1
from time import time
from typing import List
from discord import ApplicationContext
from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    DateTime,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    select,
    desc
)
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declared_attr
from utils import config
from .connect import get_session


class CivvieBotBase(DeclarativeBase):
    '''
    Base model class to inherit from.
    '''


class HasSlug:
    '''
    Mixin class providing the foreign key 'slug' and related 'webhookurl'.
    '''

    @declared_attr
    def slug(self) -> Mapped[str]:
        '''
        Foreign key relationship to the webhook_url slug.
        '''
        return mapped_column(ForeignKey('webhook_url.slug'))

    @property
    def full_url(self):
        '''
        Return the full URL that this object's slug references.
        '''
        return config.API_ENDPOINT + self.slug


class WebhookURL(HasSlug, CivvieBotBase):
    '''
    Represents a URL the API can receive turn notifications at.
    '''
    __tablename__ = 'webhook_url'

    @staticmethod
    def generate_slug():
        '''
        Generates a slug to make a webhook URL.

        This is technically liable to fail the uniqueness test, but 16^16 is a
        pretty big number 😎 so if CivvieBot starts to fail frequently on
        this, we may have bigger issues.
        '''
        hasher = sha1(str(time()).encode('UTF-8'))
        return hasher.hexdigest()[:16]

    slug: Mapped[str] = mapped_column(
        String(16),
        primary_key=True,
        default=generate_slug,
        use_existing_column=False
    )
    # The snowflake of the channel this URL operates in.
    channelid: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        unique=True
    )
    # One-to-many relationship to the tables linked back to this URL.
    games: Mapped[List['Game']] = relationship(
        back_populates='webhookurl',
        cascade='all'
    )
    players: Mapped[List['Player']] = relationship(
        back_populates='webhookurl',
        cascade='all'
    )
    turns: Mapped[List['TurnNotification']] = relationship(
        back_populates='webhookurl',
        cascade='all'
    )


class SlugRelated(HasSlug):
    '''
    Mixin class providing the 'webhookurl' relationship to the slug.
    '''
    @declared_attr
    def webhookurl(self) -> Mapped[WebhookURL]:
        '''
        Relationship to the WebhookURL provided by self.slug.
        '''
        return relationship(WebhookURL)


class NamedConvertable(SlugRelated):
    '''
    Mixin class providing a 'name', which is used as the target for a 'convert'
    method compatible with py-cord parameter conversion.
    '''
    name: Mapped[str]

    async def convert(self, ctx: ApplicationContext, arg: str):
        '''
        Converts the given string to the appropriate resource.

        Expects a webhookurl and name to be defined.
        '''
        with get_session() as session:
            scalar = session.scalar(
                select(self.__class__)
                .join(self.__class__.webhookurl)
                # Simply expect an exception if this property is not named.
                .where(self.__class__.name == arg)
                .where(WebhookURL.channelid == ctx.channel_id)
            )
        if not scalar:
            raise NoResultFound(
                'Failed to find the given resource in the database.')
        return scalar


class PlayerGames(HasSlug, CivvieBotBase):
    '''
    Maintains a many-to-many relationship between the Player and Game tables.
    '''
    __tablename__ = 'player_games'
    # Primary keys for each of the foreign keys that comprise this table.
    slug: Mapped[str] = mapped_column(
        ForeignKey('webhook_url.slug'),
        primary_key=True
    )
    playerid: Mapped[int] = mapped_column(
        ForeignKey('player.id'),
        primary_key=True
    )
    gameid: Mapped[int] = mapped_column(
        ForeignKey('game.id'),
        primary_key=True
    )
    # Relationships tied to the above primary keys.
    player: Mapped['Player'] = relationship(back_populates='games')
    game: Mapped['Game'] = relationship(back_populates='players')


class TurnNotification(SlugRelated, CivvieBotBase):
    '''
    Represents a stashed Civilization 6 turn notification.
    '''
    __tablename__ = 'turn_notification'
    # The turn number reported by this notification.
    turn: Mapped[int] = mapped_column(Integer, primary_key=True)
    # The player reported by this notification.
    playerid: Mapped[int] = mapped_column(
        ForeignKey('player.id'),
        primary_key=True
    )
    # The game reported by this notification.
    gameid: Mapped[int] = mapped_column(
        ForeignKey('game.id'),
        primary_key=True
    )
    # The slug of the URL this notification was POSTed to.
    slug: Mapped[str] = mapped_column(
        ForeignKey('webhook_url.slug'),
        primary_key=True
    )
    # The time this notification came in.
    logtime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # The last time this notification was pinged in Discord (None for never).
    lastnotified: Mapped[datetime] = mapped_column(
        DateTime,
        default=None,
        nullable=True
    )
    # One-to-many relationship to the Player table.
    player: Mapped['Player'] = relationship(
        back_populates='turns',
        lazy='immediate'
    )
    # One-to-many relationship to the Game table.
    game: Mapped['Game'] = relationship(
        back_populates='turns',
        lazy='immediate'
    )
    # One-to-many relationship to the WebhookURL table.
    webhookurl: Mapped['WebhookURL'] = relationship(
        back_populates='turns',
        lazy='immediate'
    )


class Player(NamedConvertable, CivvieBotBase):
    '''
    Represents a player being tracked in a Civilization 6 game.
    '''
    __tablename__ = 'player'
    __table_args__ = (UniqueConstraint('name', 'slug', name='player_to_slug'),)
    id: Mapped[int] = mapped_column(
        Integer,
        autoincrement=True,
        primary_key=True
    )
    # The name of this player, obtained from Civilization 6.
    name: Mapped[str] = mapped_column(String(255))
    # The slug of the URL this player was obtained from.
    slug: Mapped[str] = mapped_column(ForeignKey('webhook_url.slug'))
    # The snowflake of the Discord user this player is linked to.
    discordid: Mapped[int] = mapped_column(
        BigInteger,
        default=None,
        nullable=True
    )
    # Many-to-many relationship to the Games table via the player_games table.
    games: Mapped[List['PlayerGames']] = relationship(back_populates='player')
    # Reference relationship to the WebhookURL tracking this player.
    webhookurl: Mapped['WebhookURL'] = relationship(back_populates='players')
    # One-to-many relationship to the TurnNotification table.
    turns: Mapped[List[TurnNotification]] = relationship(
        back_populates='player',
        order_by=desc(TurnNotification.logtime)
    )


class Game(NamedConvertable, CivvieBotBase):
    '''
    Represents a game being tracked from Civilization 6.
    '''
    __tablename__ = 'game'
    # Form a unique constraint from the name and slug.
    __table_args__ = (UniqueConstraint('name', 'slug', name='game_to_slug'),)
    # Unique identifier for the game.
    id: Mapped[int] = mapped_column(
        Integer,
        autoincrement=True,
        primary_key=True
    )
    # The registered name of this game.
    name: Mapped[str] = mapped_column(String(255))
    # The slug of the webhook URL this game is registered to.
    slug: Mapped[str] = mapped_column(ForeignKey('webhook_url.slug'))
    # Whether we should pop notifications for this game at all.
    muted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Whether we have warned about detecting a duplicate game. If null, we do
    # not know of a duplicate we need to warn about.
    duplicatewarned: Mapped[bool] = mapped_column(
        Boolean,
        default=None,
        nullable=True
    )
    # How frequently turn reminders pop for this game. If null, reminders are
    # not sent.
    remindinterval: Mapped[int] = mapped_column(
        Integer,
        default=config.REMIND_INTERVAL
    )
    # Helper datetime calculated at time of notification; holds the time we
    # should ping next.
    nextremind: Mapped[datetime] = mapped_column(
        DateTime,
        default=None,
        nullable=True
    )
    # Notifications and reminders will not pop for a game whose current turn is
    # under this number.
    minturns: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=config.MIN_TURNS
    )
    # One-to-one relationship to the WebhookURL table.
    webhookurl: Mapped['WebhookURL'] = relationship(
        back_populates='games',
        lazy='immediate'
    )
    # Many-to-many relationship to the Player table via the player_games table.
    players: Mapped[List['PlayerGames']] = relationship(
        back_populates='game',
        cascade='save-update, merge, delete, delete-orphan'
    )
    # One-to-many relationship to the TurnNotification table.
    turns: Mapped[List[TurnNotification]] = relationship(
        back_populates='game',
        cascade='save-update, merge, delete, delete-orphan',
        order_by=desc(TurnNotification.logtime)
    )
