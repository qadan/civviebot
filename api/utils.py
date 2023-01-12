'''
Helpers for the API.
'''

import logging
from datetime import datetime
from flask import Response, request
from database.models import TurnNotification, Player, Game
from database.utils import get_session

logger = logging.getLogger(f'civviebot.api.{__name__}')
# In most cases, we just want to say 'yes we got a message' and end with no
# claim as to status. We can't talk to Civ 6, and it doesn't care what we
# return. Anyone who would care is spoofing calls, and we don't want to
# communicate this. So, this is the response to ALL calls.
JUST_ACCEPT = Response(response='Accepted', status=200)

async def request_source_is_civ_6():
    '''
    Validates that the source of a Request object is, as best we can tell, actually coming from
    Civilization 6.
    '''
    logger.debug(request.headers)
    logger.debug(await request.get_json())
    return True

def register_turn(player: Player, game: Game, turn_number: int):
    '''
    Registers a turn in the database with the given player ID and turn number.
    '''
    with get_session():
        return TurnNotification(player=player, game=game, turn=turn_number, logtime=datetime.now())
