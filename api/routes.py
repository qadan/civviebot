'''
Routes that serve the API.
'''

import logging
from datetime import datetime
from operator import itemgetter
from os import environ
from discord import Permissions
from discord.utils import oauth_url
from flask import Blueprint, request, render_template
from sqlalchemy import select
from database.models import WebhookURL, Player, Game
from database.utils import get_session
from api import utils as api_utils
from utils import config

logger = logging.getLogger(f'civviebot.api.{__name__}')
api_blueprint = Blueprint('routes', __name__)

@api_blueprint.route('/civ6/<string:slug>', methods=['GET'])
async def slug_get():
    '''
    Provide help if the endpoint is requested as GET.
    '''
    return await render_template('slug_to_page.j2', year=datetime.now().year), 200

async def get_body_json():
    '''
    Attempts to parse the incoming body as JSON.
    '''
    body = await request.get_json()
    if not body:
        raise ValueError('Failed to parse JSON')
    playername, gamename, turnnumber = itemgetter(
        'value1', 'value2', 'value3')(body)
    if not playername or not gamename or not turnnumber:
        raise ValueError('JSON was missing keys')
    return (playername, gamename, turnnumber)

@api_blueprint.route('/civ6/<string:slug>', methods=['POST'])
async def incoming_civ6_request(slug):
    '''
    Process an individual request.
    '''
    # Basic test for source.
    if not await api_utils.request_source_is_civ_6():
        return api_utils.JUST_ACCEPT

    playername: str
    gamename: str
    turnnumber: int
    try:
        playername, gamename, turnnumber = await get_body_json()
    except ValueError:
        return api_utils.JUST_ACCEPT

    with get_session() as session:
        url = session.scalar(
            select(WebhookURL).where(WebhookURL.slug == slug))
    if not url:
        # This is not a real slug.
        return api_utils.JUST_ACCEPT

    with get_session() as session:
        game = session.scalar(
            select(Game).where(
                Game.name == gamename
                and Game.slug == url.slug))
    if not game:
        # This game is not in the allowlist and we should leave.
        return api_utils.JUST_ACCEPT

    if game.turns and game.turns[0].turn > turnnumber:
        logger.warning('Duplicate-named game detected for "%s" obtained from webhook URL %s',
            game.name,
            url.slug)
        if game.duplicatewarned is None:
            logger.warning(
                'No duplicate notification for "%s" has been sent; flagging to notify',
                game.name)
            game.duplicatewarned = False
        return api_utils.JUST_ACCEPT

    # Check for the player, create if needed.
    with get_session() as session:
        player = session.scalar(
            select(Player).where(
                Player.name == playername
                and Player.slug == slug))
        if not player:
            player = Player(
                playername=playername,
                gamename=gamename,
                urlslug=slug)
            logger.info('Tracking new player %s in game %s obtained from webhook URL %s',
                playername,
                gamename,
                slug)
    # This case represents a new turn.
    if game.turns[0].turn < turnnumber:
        logger.info('Tracking new turn %d in game %s obtained from webhook URL %s',
            turnnumber,
            gamename,
            slug)
    # Register a new turn.
    api_utils.register_turn(player, game, turnnumber)

    # If we got here, log and respond with 202.
    logger.info(('Successful notification from Civilization 6 logged: %s in game "%s" at turn %d '
        '(tracked in channel: %s)'),
        playername,
        gamename,
        turnnumber,
        url.channelid)
    return api_utils.JUST_ACCEPT

@api_blueprint.errorhandler(404)
async def send_help(error):
    '''
    On 404, we actually send a 200 with the main help template.
    '''
    logger.info('Sending a help page: %s', error)
    if request.headers.get('Content-Type', '') == 'application/json':
        return api_utils.JUST_ACCEPT
    bot_perms = Permissions()
    bot_perms.send_messages = True
    bot_perms.send_messages_in_threads = True
    bot_perms.view_channel = True
    invite_link = oauth_url(
        client_id=environ.get('DISCORD_CLIENT_ID'),
        permissions=bot_perms,
        scopes=('bot', 'applications.commands'))
    return await render_template(
        'help.j2',
        oauth_url=invite_link,
        command_prefix=config.COMMAND_PREFIX,
        year=datetime.now().year), 200
