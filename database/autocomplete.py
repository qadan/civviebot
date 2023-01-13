'''
Autocomplete functions to let slash commands query the database.
'''

from typing import Type
from discord import AutocompleteContext
from sqlalchemy import select, Select
from database.models import Game, Player, WebhookURL, CivvieBotBase
from database.utils import get_session

def _base_model_select(model: Type[CivvieBotBase], channel_id: int, value: str) -> Select:
    '''
    Provides the base select for an item of a specified model in a channel.
    '''
    return (select(model)
        .join(model.webhookurl)
        .where(WebhookURL.channelid == channel_id)
        .where(model.name.like(f'%{value}%')))

def get_games_for_channel(ctx: AutocompleteContext) -> str:
    '''
    Autocomplete to return games in the context channel.
    '''
    game_select = _base_model_select(Game, ctx.interaction.channel_id, ctx.value)
    with get_session() as session:
        for result in session.scalars(game_select).all():
            yield result.name

def get_players_for_channel(ctx: AutocompleteContext) -> str:
    '''
    Autocomplete to return players in the context channel.
    '''
    player_select = _base_model_select(Player, ctx.interaction.channel_id, ctx.value)
    with get_session() as session:
        for result in session.scalars(player_select).all():
            yield result.name

def get_unlinked_players_for_channel(ctx: AutocompleteContext) -> str:
    '''
    Autocomplete to return unlinked players in the context channel.
    '''
    player_select = (_base_model_select(Player, ctx.interaction.channel_id, ctx.value)
        .where(Player.discordid == None))
    with get_session() as session:
        for result in session.scalars(player_select).all():
            yield result.name

def get_linked_players_for_channel(ctx: AutocompleteContext) -> str:
    '''
    Autocomplete to return players linked to a user in the context channel.
    '''
    player_select = (_base_model_select(Player, ctx.interaction.channel_id, ctx.value)
        .where(Player.discordid != None))
    with get_session() as session:
        for result in session.scalars(player_select).all():
            yield result.name

def get_self_linked_players_for_channel(ctx: AutocompleteContext) -> str:
    '''
    Autocomplete to return players linked to the initiating user in the context channel.
    '''
    player_select = (_base_model_select(Player, ctx.interaction.channel_id, ctx.value)
        .where(Player.discordid == ctx.interaction.user.id))
    with get_session() as session:
        for result in session.scalars(player_select).all():
            yield result.name
