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


civviebot_api = Quart(__name__)
logger = logging.getLogger(f'civviebot.{__name__}')


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
        permissions=bot_perms)
    return await render_template(
        'help.j2',
        oauth_url=invite_link,
        command_prefix=config.get('command_prefix'),
        year=datetime.date.today().year), 200


@civviebot_api.route('/civ6/<string:slug>', methods=['POST', 'GET'])
async def incoming_civ6_request(slug):
    '''
    Process an individual request from Civilization 6.
    '''
    if request.method == 'GET':
        return await render_template('slug_to_page.j2', year=datetime.date.today().year), 200
    body = await request.get_json()
    playername, gamename, turnnumber = itemgetter(
        'value1', 'value2', 'value3')(body)
    if not playername or not gamename or not turnnumber:
        return error("Invalid JSON; missing one or more keys", 400)

    if not request_source_is_civ_6():
        return error("Not authorized; request must come from Civilization 6", 401)

    with db_session():
        try:
            url = models.WebhookURL[slug]
        except ObjectNotFound:
            abort(404)

        game = models.Game.get(gamename=gamename, webhookurl=url)
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
                webhookurl=url,
                minturns=url.minturns,
                notifyinterval=url.notifyinterval)
            logger.info('Tracking new game %s obtained from webhook URL %s',
                game.gamename,
                url.slug)
        game.lastturn = time()
        game.turn = turnnumber
        player = models.Player.get(lambda p: p.playername == playername and game in p.games)
        if not player:
            player = models.Player(playername=playername, games=[game])
            logger.info('Tracking new player %s in game %s obtained from webhook URL %s',
                player.playername,
                game.gamename,
                url.slug)
        game.lastup = player
    logger.info('New turn: %s in game "%s" at turn %d (tracked in channel: %s)',
        playername,
        gamename,
        turnnumber,
        url.channelid)
    return Response(response='Accepted', status=202)
