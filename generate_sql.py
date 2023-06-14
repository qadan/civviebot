'''
A utility script to generate the SQL in database/civviebot.sql.

This only exists as a deployment step for Docker and shouldn't otherwise be
used.
'''

from os import path, remove
from sqlalchemy.schema import CreateTable
from database.connect import get_db
from database.models import (
    WebhookURL,
    Game,
    Player,
    PlayerGames,
    TurnNotification
)

engine = get_db()
destination = path.join(
    path.dirname(path.realpath(__file__)),
    'database',
    'sql',
    'tables.sql'
)

if path.isfile(destination):
    remove(destination)

for idx, model in enumerate(
    [WebhookURL, Game, Player, PlayerGames, TurnNotification]
):
    with open(destination, mode='a', encoding='utf-8') as sqlfile:
        sqlfile.write(str(CreateTable(model.__table__).compile(engine)))
