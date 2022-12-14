'''
Models for types of entities in CivvieBot's database.
'''

from pony.orm.core import PrimaryKey, Required, Set, Optional
from utils import config
from .utils import get_db


db = get_db()
min_turns = config.get('min_turns', 30)
max_downtime = config.get('stale_notification_length', 604800)


class WebhookURL(db.Entity):
    '''
    Represents a webhook URL generated in a channel that Civilization 6 can communicate with.
    '''

    # Slug is a 12-digit hex code hashed from Unix time, so this will be fine for now. Once everyone
    # on earth makes like hundreds of thousands of URLs, we can look into expanding this to 13.
    slug = PrimaryKey(str, 12)
    # The IDs we get from ApplicationContext are integers, but they are regularly longer than the
    # limit for (int). There may be a more graceful way of handling this naturally that would
    # require digging through Pony's docs.
    channelid = Required(str)
    # Configurable minimum turns, which games then inherit.
    minturns = Required(int, default=min_turns)
    # Configurable notification interval, which games then inherit.
    notifyinterval = Required(int, default=max_downtime)
    # One-to-many relationship to the Game table.
    games = Set('Game', cascade_delete=True)


class Player(db.Entity):
    '''
    Represents a player, possibly linked to a Discord ID, reported to CivvieBot by Civilization 6.
    '''
    # Player names could be duplicates so maintaining our own index.
    id = PrimaryKey(int, auto=True)
    # Obtained from Civ 6 and stashed.
    playername = Required(str)
    # Obtained when a Discord user claims a player as their own.
    discordid = Optional(str)
    # Many-to-many relationship to the Game table.
    games = Set('Game', reverse='players')
    # Many-to-one relationship to the Game table specifying which ones the player is 'up' in.
    upin = Set('Game', reverse='lastup')


class Game(db.Entity):
    '''
    Represents an ongoing game reported to CivvieBot by Civilization 6.
    '''
    # Game names could be duplicates so maintaining our own index.
    id = PrimaryKey(int, auto=True)
    # Obtained from Civ 6 and stashed.
    gamename = Required(str)
    # Obtained from Civ 6 and updated at that time.
    turn = Required(int, default=0)
    # Timestamp of when the last turn popped.
    lastturn = Optional(float)
    # The last time a notification was sent out for this game.
    lastnotified = Optional(float, default=0.0)
    # Whether we should pop notifications for this game.
    muted = Required(bool, default=False)
    # Maximum downtime. Inherit from WebhookURL.
    notifyinterval = Required(int)
    # Minimum turns. Inherit from WebhookURL.
    minturns = Required(int)
    # Many-to-many relationship to the Player table.
    players = Set(Player)
    # One-to-many relationship to the Player table, specifying the last player Civ 6 told us was up.
    lastup = Optional(Player)
    # Many-to-one relationship to the WebhookURL table.
    webhookurl = Required(WebhookURL)
