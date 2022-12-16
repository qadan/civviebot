'''
API for receiving incoming requests from Civilization 6.
'''

import logging
from operator import itemgetter
from time import time
from pony.orm import db_session
from quart import Quart, request, Response, abort
from database import models

# @TODO:
# - How to determine source is civ 6 (probably incoming url/agent check)
# - What if someone hits the link

civviebot_api = Quart(__name__)


def error(message: str, status: int):
    '''
    Helper function to format a message and status string and integer as a Response
    '''
    return Response(response=message, status=status)


def request_source_is_civ_6():
    '''
    Validates that the source of a Request object is, as best we can tell, actually coming from
    Civilization 6.
    '''
    return True


def as_page(slug):
    '''
    Returns the template for a given page. We don't actually validate the slug.
    '''
    return slug


@civviebot_api.route('/civ6/<string:slug>', methods=['POST', 'GET'])
async def incoming_civ6_request(slug):
    '''
    Process an individual request from Civilization 6.
    '''
    if request.method == 'GET':
        return as_page(slug)
    body = await request.get_json()
    playername, gamename, turnnumber = itemgetter(
        'value1', 'value2', 'value3')(body)
    if not playername or not gamename or not turnnumber:
        return error("Invalid JSON; missing one or more keys", 400)

    if not request_source_is_civ_6():
        return error("Not authorized; request must come from Civilization 6", 401)

    with db_session():
        webhook = models.WebhookURL.get(slug=slug)
        if not webhook:
            abort(404)

        game = models.Game.get(gamename=gamename, webhookurl=webhook)
        if game:
            if game.turn > turnnumber:
                # This is an exceptional case; we have two identically named games for
                # the same URL, so we can't make the second one.
                return error('''
                Attempting to create a game when one already exists by this name on this server''',
                400)
            if game.turn == turnnumber:
                # Handling multiple requests from different webhooks.
                return 'Already created', 304
        else:
            game = models.Game(
                gamename=gamename,
                webhookurl=webhook,
                minturns=webhook.minturns,
                notifyinterval=webhook.notifyinterval)
            logging.info('Tracking new game %s obtained from webhook URL %s',
                game.gamename,
                webhook.slug)
        game.lastturn = time()
        game.turn = turnnumber
        player = models.Player.get(lambda p: p.playername == playername and game in p.games)
        if not player:
            player = models.Player(playername=playername, games=[game])
            logging.info('Tracking new player %s in game %s obtained from webhook URL %s',
                player.playername,
                game.gamename,
                webhook.slug)
        game.lastup = player
    logging.info((f'New turn: {playername} in game "{gamename}" at turn {turnnumber} (tracked in '
        f'channel: {webhook.channelid})'))
    return Response(response='Accepted', status=202)
