'''
Routes that serve the API.
'''

import logging
from datetime import datetime
from operator import itemgetter
from os import environ
from discord import Permissions
from discord.utils import oauth_url
from flask import Blueprint, request, render_template, Response
from sqlalchemy import select
from database.models import TurnNotification, WebhookURL, Player, Game, PlayerGames
from database.utils import get_session
from utils import config

logger = logging.getLogger(f'civviebot.api.{__name__}')
api_blueprint = Blueprint('routes', __name__)

# In most cases, we just want to say 'yes we got a message' and end with no
# claim as to status. We can't talk to Civ 6, and it doesn't care what we
# return. Anyone who would care is spoofing calls, and we don't want to
# communicate this. So, this is the response to ALL calls.
JUST_ACCEPT = Response(response='Accepted', status=200)

def request_source_is_civ_6():
    '''
    Validates that the source of a Request object is, as best we can tell, actually coming from
    Civilization 6.
    '''
    logger.debug(request.headers)
    logger.debug(request.get_json())
    return True

@api_blueprint.route('/')
def send_help():
    '''
    Send a help page at the front page.
    '''
    if request.headers.get('Content-Type', '') == 'application/json':
        return JUST_ACCEPT
    bot_perms = Permissions()
    bot_perms.send_messages = True
    bot_perms.send_messages_in_threads = True
    bot_perms.view_channel = True
    invite_link = oauth_url(
        client_id=environ.get('DISCORD_CLIENT_ID'),
        permissions=bot_perms,
        scopes=('bot', 'applications.commands'))
    return render_template(
        'help.j2',
        oauth_url=invite_link,
        command_prefix=config.COMMAND_PREFIX,
        year=datetime.now().year), 200

@api_blueprint.route('/civ6/<string:slug>', methods=['GET'])
def slug_get(slug):
    '''
    Provide help if the endpoint is requested as GET.
    '''
    return render_template('slug_to_page.j2', slug=slug, year=datetime.now().year), 200

def get_body_json():
    '''
    Attempts to parse the incoming body as JSON.
    '''
    body = request.get_json()
    if not body:
        raise ValueError('Failed to parse JSON')
    playername, gamename, turnnumber = itemgetter(
        'value1', 'value2', 'value3')(body)
    if not playername or not gamename or not turnnumber:
        raise ValueError('JSON was missing keys')
    return (playername, gamename, turnnumber)

@api_blueprint.route('/civ6/<string:slug>', methods=['POST'])
def incoming_civ6_request(slug):
    '''
    Process an individual request.
    '''
    # Basic test for source.
    if not request_source_is_civ_6():
        logger.debug('Request to %s could not be validated as sourced from Civ 6', slug)
        return JUST_ACCEPT

    playername: str
    gamename: str
    turnnumber: int
    try:
        playername, gamename, turnnumber = get_body_json()
    except ValueError:
        logger.debug('Invalid request: %s', get_body_json())
        return JUST_ACCEPT

    with get_session() as session:
        url = session.scalar(
            select(WebhookURL).where(WebhookURL.slug == slug))
        if not url:
            # This is not a real slug.
            logger.debug('Valid request to invalid slug %s', slug)
            return JUST_ACCEPT

        game = session.scalar(
            select(Game).where(Game.name == gamename).where(Game.slug == url.slug))
        if not game:
            # This game is not in the allowlist and we should leave.
            logger.debug('Valid request to valid slug %s references untracked game %s',
                slug,
                gamename)
            return JUST_ACCEPT

        if game.turns and game.turns[0].turn > turnnumber:
            logger.info('Duplicate-named game detected for "%s" obtained from webhook URL %s',
                game.name,
                url.slug)
            if game.duplicatewarned is None:
                logger.info(
                    'No duplicate notification for "%s" has been sent; flagging to notify',
                    game.name)
                game.duplicatewarned = False
            return JUST_ACCEPT

        # Check for the player, create if needed.
        player = session.scalar(
            select(Player).where(Player.name == playername).where(Player.slug == slug))
        if not player:
            player = Player(
                name=playername,
                slug=slug)
            session.add(player)
            player_game = PlayerGames(
                gamename=game.name,
                playername=playername,
                slug=slug)
            session.add(player_game)
            player.games.append(player_game)
            logger.info('Tracking new player %s in game %s obtained from webhook URL %s',
                playername,
                gamename,
                slug)
        # Register a new turn.
        notification = TurnNotification(
            playername=player.name,
            gamename=game.name,
            turn=turnnumber,
            slug=slug,
            logtime=datetime.now())
        session.add(notification)
        session.commit()

        # If we got here, log and accept.
        logger.info(('Notification from Civilization 6 validated and logged: %s in game "%s" at '
            'turn %d (tracked in channel: %s)'),
            playername,
            gamename,
            turnnumber,
            url.channelid)
    return JUST_ACCEPT
