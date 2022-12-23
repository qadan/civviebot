'''
API for receiving incoming requests from Civilization 6.
'''

import datetime
import logging
from operator import itemgetter
from time import time
from discord import Permissions
from discord.utils import oauth_url
from pony.orm import db_session, ObjectNotFound
from quart import Quart, request, Response, abort, render_template
from database import models
from utils import config
from utils.utils import generate_url


civviebot_api = Quart(__name__)
logger = logging.getLogger(f'civviebot.{__name__}')
EPOCH = datetime.datetime.utcfromtimestamp(0)


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


@civviebot_api.errorhandler(404)
async def send_help():
    '''
    On 404, we actually send a 200 with the main help template.
    '''
    bot_perms = Permissions()
    bot_perms.send_messages = True
    bot_perms.send_messages_in_threads = True
    bot_perms.view_channel = True
    invite_link = oauth_url(
        client_id=config.get('discord_client_id'),
        permissions=bot_perms,
        scopes=('bot', 'applications.commands'))
    return await render_template(
        'help.j2',
        oauth_url=invite_link,
        command_prefix=config.get('command_prefix'),
        year=datetime.date.today().year), 200


@civviebot_api.route('/civ6/<string:slug>', methods=['POST', 'GET'])
async def incoming_civ6_request(slug):
    '''
    Process an individual request.
    '''
    # If this is a GET request, provide some documentation.
    if request.method == 'GET':
        return await render_template('slug_to_page.j2', year=datetime.date.today().year), 200
    
    # Basic 
    if not request_source_is_civ_6():
        return error("Not authorized; request must come from Civilization 6", 401)
    
    # Parse and validate JSON.
    body = await request.get_json()
    if not body:
        return error("Invalid request; expected JSON.", 400)
    playername, gamename, turnnumber = itemgetter(
        'value1', 'value2', 'value3')(body)
    if not playername or not gamename or not turnnumber:
        return error("Invalid JSON; missing one or more keys", 400)

    with db_session():
        # If the URL is invalid, provide help.
        try:
            url = models.WebhookURL[slug]
        except ObjectNotFound:
            abort(404)
                    
        # Create/update the game.
        game = models.Game.get(gamename=gamename, webhookurl=url)
        if not game:
            game = models.Game(
                gamename=gamename,
                webhookurl=url,
                minturns=url.minturns,
                notifyinterval=url.notifyinterval)
            logger.info('Tracking new game %s obtained from webhook URL %s',
                game.gamename,
                url.slug)
        # Check for the player. 
        player = models.Player.get(lambda p: p.playername == playername and game in p.games)
        # Bail early if this is a duplicate turn.
        if player and player.id in game.currentturn:
            return error('Notification already sent', 409)
        if not player:
            # This is an exceptional case; it appears someone started a new game
            # with the same name for the same URL.
            if game.turn > turnnumber:
                if game.warnedduplicate is None:
                    game.warnedduplicate = False
                logger.warn('Duplicate-named game detected for "%s" obtained from webhook URL %s',
                    game.gamename,
                    generate_url(url))
                return error('Duplicate game detected', 400)
            player = models.Player(playername=playername, games=[game])
            logger.info('Tracking new player %s in game %s obtained from webhook URL %s',
                player.playername,
                game.gamename,
                url.slug)

        # Update the game.
        if game.turn < turnnumber:
            game.pinged = []
        game.pinged.append(player.id)
        game.turn = turnnumber
        game.lastup = player
        game.lastturn = (request.date - EPOCH).total_seconds()

    # If we got here, log and respond with 202.
    logger.info('New notification: %s in game "%s" at turn %d (tracked in channel: %s)',
        playername,
        gamename,
        turnnumber,
        url.channelid)
    return Response(response='Accepted', status=202)

def set_player_order(game: models.Game, player: models.Player):
    '''
    Attempts to set game.playerorder.
    '''
