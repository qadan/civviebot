'''
Routes that serve the API.
'''

import logging
from datetime import datetime
from operator import itemgetter
from discord import Permissions
from discord.utils import oauth_url
from flask import Blueprint, request, render_template, Response
from sqlalchemy import select
from database.models import (
    TurnNotification,
    WebhookURL,
    Player,
    Game,
    PlayerGames
)
from database.connect import get_session
from utils import config


logger = logging.getLogger(f'civviebot.api.{__name__}')
api_blueprint = Blueprint('routes', __name__)


# In most cases, we just want to say 'yes we got a message' and end with no
# claim as to status. We can't talk to Civ 6, and it doesn't care what we
# return. Anyone who would care is spoofing calls, which we don't want to
# communicate that we know. So, this is the response to ALL calls.
JUST_ACCEPT = Response(response='Accepted', status=200)


def request_source_is_civ_6():
    '''
    Validates that the source of a Request object is, as best we can tell,
    actually coming from Civilization 6.

    @TODO: How feasible is this even? Test.
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
        client_id=config.DISCORD_CLIENT_ID,
        permissions=bot_perms,
        scopes=('bot', 'applications.commands')
    )
    return render_template(
        'help.j2',
        oauth_url=invite_link,
        command_prefix=config.COMMAND_PREFIX,
        year=datetime.now().year
    ), 200


@api_blueprint.route('/civ6/<string:slug>', methods=['GET'])
def slug_get(slug):
    '''
    Provide help if the endpoint is requested as GET.
    '''
    del slug
    return render_template('slug_to_page.j2', year=datetime.now().year), 200


def get_body_json():
    '''
    Attempts to parse the incoming body as JSON.
    '''
    body = request.get_json()
    if not body:
        raise ValueError('Failed to parse JSON')
    gamename, playername, turnnumber = itemgetter(
        'value1',
        'value2',
        'value3'
    )(body)
    if not gamename or not playername or not turnnumber:
        raise ValueError('JSON was missing keys')
    return (gamename, playername, turnnumber)


@api_blueprint.route('/civ6/<string:slug>', methods=['POST'])
def incoming_civ6_request(slug):
    '''
    Process an individual request.
    '''
    # Basic test for source.
    if not request_source_is_civ_6():
        logger.debug(
            'Request to %s could not be validated as sourced from Civ 6',
            slug
        )
        return JUST_ACCEPT

    gamename: str
    playername: str
    turnnumber: int
    try:
        gamename, playername, turnnumber = get_body_json()
    except ValueError:
        logger.debug('Invalid request: %s', get_body_json())
        return JUST_ACCEPT

    with get_session() as session:
        channel_id, _ = session.execute(
            select(WebhookURL.channelid, WebhookURL.slug)
            .where(WebhookURL.slug == slug)
        ).first().tuple()
        if not channel_id:
            # This is not a real slug.
            logger.debug('Valid request to invalid slug %s', slug)
            return JUST_ACCEPT

        game = session.scalar(
            select(Game)
            .where(Game.name == gamename)
            .where(Game.slug == slug)
        )
        if not game:
            # This game is not in the allowlist and we should leave.
            logger.debug(
                'Valid request to %s references untracked game %s',
                slug,
                gamename
            )
            return JUST_ACCEPT

        if game.turns and game.turns[0].turn > turnnumber:
            logger.info(
                'Duplicate game detected (%s) obtained from webhook URL %s',
                game.name,
                slug
            )
            if game.duplicatewarned is None:
                logger.info(
                    'Flagging %s for ',
                    game.name
                )
                game.duplicatewarned = False
            return JUST_ACCEPT

        # Check for the player, create if needed.
        player = session.scalar(
            select(Player)
            .where(Player.name == playername)
            .where(Player.slug == slug)
        )
        if not player:
            player = Player(
                name=playername,
                slug=slug
            )
            session.add(player)
            session.commit()
            player_game = PlayerGames(
                gameid=game.id,
                playerid=player.id,
                slug=slug
            )
            session.add(player_game)
            player.games.append(player_game)
            session.commit()
            logger.info(
                'Tracking new player %s in game %s from webhook URL %s',
                playername,
                gamename,
                slug
            )
        # Register a new turn.
        notification = TurnNotification(
            playerid=player.id,
            gameid=game.id,
            turn=turnnumber,
            slug=slug,
            logtime=datetime.now()
        )
        session.add(notification)
        session.commit()

        # If we got here, log and accept.
        logger.info(
            ('Notification from Civilization 6 validated and logged: %s in '
             'game "%s" at turn %d (tracked in channel: %s)'),
            playername,
            gamename,
            turnnumber,
            channel_id
        )
    return JUST_ACCEPT
