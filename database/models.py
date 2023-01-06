'''
Models for types of entities in CivvieBot's database.

N.B. You will see IDs in these models that one would think should be stored as integers but are
actually stored as strings. This is because Discord snowflakes, while integers, are often 'higher'
than the limit of simple Python integers. 1.1 is slated to migrate away from Pony, hopefully helping
alleviate this issue.
'''

from pony.orm.core import PrimaryKey, Required, Set, Optional
from utils import config
from .utils import get_db

db = get_db()
min_turns = config.MIN_TURNS
max_downtime = config.STALE_GAME_LENGTH

class WebhookURL(db.Entity):
    '''
    Represents a webhook URL generated in a channel that Civilization 6 can communicate with.
    '''
    # Slug is a 12-digit hex code hashed from Unix time, so this will be fine
    # for now. Once everyone on earth makes like hundreds of thousands of URLs,
    # we can look into expanding this to 13.
    slug = PrimaryKey(str, 12)
    # The snowflake of the channel this URL works in.
    channelid = Required(str)
    # Configurable minimum turns, which games then inherit.
    minturns = Required(int, default=min_turns)
    # Configurable notification interval, which games then inherit.
    notifyinterval = Optional(float, default=max_downtime)
    # One-to-many relationship to the Game table.
    games = Set('Game', cascade_delete=True)
    # Whether this webhook URL is flagged for deletion and will be cleaned up.
    cleanup = Required(bool, default=False)
    # Whether we have warned about the 25 Game limit. If None, we should not
    # warn.
    warnedlimit = Optional(bool, default=None, nullable=True)

class Player(db.Entity):
    '''
    Represents a player, possibly linked to a Discord ID, reported to CivvieBot by Civilization 6.
    '''
    # Player names could be duplicates (between games) so maintaining our own
    # index.
    id = PrimaryKey(int, auto=True)
    # Obtained from Civ 6 and stashed.
    playername = Required(str)
    # The snowflake of the Discord user this player is linked to. An empty
    # string represents no link.
    discordid = Optional(str, default='')
    # Many-to-many relationship to the Game table specifying which ones the
    # player is part of.
    games = Set('Game', reverse='players')
    # Many-to-one relationship to the Game table specifying which ones the
    # player is 'up' in.
    upin = Set('Game', reverse='lastup')
    # Many-to-many relationship to the Game table specifying which ones the
    # player has already been pinged in for this turn.
    pingedin = Set('Game', reverse='pinged')
    # Whether this player is flagged for deletion and will be cleaned up.
    cleanup = Required(bool, default=False)

class Game(db.Entity):
    '''
    Represents an ongoing game reported to CivvieBot by Civilization 6.
    '''
    # Game names could be duplicates so maintaining our own index.
    id = PrimaryKey(int, auto=True)
    # Game name. Obtained from Civ 6 and stashed. Expected to be unique within
    # a URL (worth foreign keying later).
    gamename = Required(str)
    # Current turn. Obtained from Civ 6 and updated at that time.
    turn = Required(int, default=0)
    # Timestamp of when the last turn notification was received from Civ 6.
    lastturn = Optional(float)
    # The last time CivvieBot sent out a notification for this game.
    lastnotified = Optional(float, default=0.0)
    # Whether we should pop notifications for this game at all.
    muted = Required(bool, default=False)
    # Whether we have warned about detecting a duplicate game. If None, we do
    # not know of a duplicate we need to warn about.
    warnedduplicate = Optional(bool, default=None, nullable=True)
    # Maximum downtime. Inherit from WebhookURL.
    notifyinterval = Required(float)
    # Minimum turns. Inherit from WebhookURL.
    minturns = Required(int)
    # Many-to-many relationship to the Player table tracking who is part of the
    # game.
    players = Set(Player)
    # Many-to-many relationship to the Player table tracking who has been pinged
    # this turn.
    pinged = Set(Player)
    # One-to-many relationship to the Player table, specifying the last player
    # Civ 6 told us was up.
    lastup = Optional(Player)
    # Many-to-one relationship to the WebhookURL table.
    webhookurl = Required(WebhookURL)

db.generate_mapping(create_tables=True)
