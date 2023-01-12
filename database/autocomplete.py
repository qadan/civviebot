'''
Autocomplete functions to let slash commands query the database.
'''

from discord import AutocompleteContext
from sqlalchemy import select
from database.models import Game, Player, WebhookURL
from database.utils import get_session

def get_games_for_channel(ctx: AutocompleteContext) -> str:
    '''
    Autocomplete to return games in the context channel.
    '''
    with get_session() as session:
        for result in session.scalars(select(Game)
            .join(Game.webhookurl)
            .where(WebhookURL.channelid == ctx.interaction.channel_id)
            .where(Game.name.like(f'%{ctx.value}%'))).all():
            yield result.name

def get_players_for_channel(ctx: AutocompleteContext) -> str:
    '''
    Autocomplete to return players in the context channel.
    '''
    with get_session() as session:
        for result in session.scalars(select(Player)
            .join(Player.webhookurl)
            .where(WebhookURL.channelid == ctx.interaction.channel_id)
            .where(Player.name.like(f'%{ctx.value}%'))).all():
            yield result.name

def get_linked_players_for_channel(ctx: AutocompleteContext) -> str:
    '''
    Autocomplete to return players linked to the initiating user in the context channel.
    '''
    with get_session() as session:
        for result in session.scalars(select(Player)
            .join(Player.webhookurl)
            .where(Player.discordid == ctx.interaction.user.id)
            .where(WebhookURL.channelid == ctx.interaction.channel_id)).all():
            yield result.name
