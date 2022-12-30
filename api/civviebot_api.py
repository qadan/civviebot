'''
API for receiving incoming requests from Civilization 6.
'''

import datetime
import logging
from operator import itemgetter
from time import time
from discord import Permissions
from discord.utils import oauth_url
from pony.orm import db_session, ObjectNotFound, commit
from quart import Quart, request, Response, abort, render_template
from database import models
from utils import config


civviebot_api = Quart(__name__)
logger = logging.getLogger(f'civviebot.{__name__}')


def send_error(message: str, status: int):
    '''
    Helper function to format a message and status string and integer as a Response
    '''
    return Response(response=message, status=status)


async def request_source_is_civ_6():
    '''
    Validates that the source of a Request object is, as best we can tell, actually coming from
    Civilization 6.
    '''
    print(request.headers)
    print(await request.get_json())
    return True


@civviebot_api.errorhandler(404)
async def send_help(error):
    '''
    On 404, we actually send a 200 with the main help template.
    '''
    logger.info('Sending a help page: %s', error)
    if request.headers.get('Content-Type', '') == 'application/json':
        return send_error(('Unsure how to handle this request; try pasting the link in a browser '
            'for more information'), 400)
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
    
    # Basic test for source.
    if not await request_source_is_civ_6():
        return send_error("Not authorized; request must come from Civilization 6", 401)
    
    # Parse and validate JSON.
    body = await request.get_json()
    if not body:
        return send_error("Invalid request; expected JSON.", 400)
    playername, gamename, turnnumber = itemgetter(
        'value1', 'value2', 'value3')(body)
    if not playername or not gamename or not turnnumber:
        return send_error("Invalid JSON; missing one or more keys", 400)

    with db_session():
        # If the URL is invalid, provide help.
        try:
            url = models.WebhookURL[slug]
        except ObjectNotFound:
            abort(404)
                    
        # Create/update the game.
        game = models.Game.get(gamename=gamename, webhookurl=url)
        if not game:
            print(len(url.games))
            if len(url.games) < 25:
                url.warnedlimit = False if len(url.games) == 24 else None
                game = models.Game(
                    gamename=gamename,
                    webhookurl=url,
                    minturns=url.minturns,
                    notifyinterval=url.notifyinterval,
                    lastnotified=0)
                commit()
                logger.info('Tracking new game %s obtained from webhook URL %s',
                    game.gamename,
                    url.slug)
            else:
                logger.warn(('Not tracking new game %s obtained from webhook URL %s as the game '
                    'limit has been reached for this URL'),
                    gamename,
                    url.slug)
                return send_error('Game limit reached for this URL', 409)
        # This is an exceptional case; it appears someone started a new game
        # with the same name for the same URL.
        if game.turn > turnnumber:
            logger.warn('Duplicate-named game detected for "%s" obtained from webhook URL %s',
                game.gamename,
                url.slug)
            if game.warnedduplicate is None:
                logger.warn('No duplicate notification for "%s" has been sent; flagging to notify',
                    game.gamename)
                game.warnedduplicate = False
            return send_error('Duplicate game detected', 400)
        # Check for the player, create if needed.
        player = models.Player.get(lambda p: p.playername == playername and game in p.games)
        if not player:
            player = models.Player(playername=playername, games=[game])
            commit()
            logger.info('Tracking new player %s in game %s obtained from webhook URL %s',
                player.playername,
                game.gamename,
                url.slug)
        # This case represents a new turn.
        if game.turn < turnnumber:
            game.pinged = []
        # Bail if this notification has already been sent.
        elif player.id in game.pinged:
            return send_error('Notification already sent', 409)
        # Update the rest of the game info.
        game.turn = turnnumber
        game.lastup = player
        game.lastturn = time()

    # If we got here, log and respond with 202.
    logger.info(('Successful notification from Civilization 6 logged: %s in game "%s" at turn %d '
        '(tracked in channel: %s)'),
        playername,
        gamename,
        turnnumber,
        url.channelid)
    return Response(response='Accepted', status=202)
