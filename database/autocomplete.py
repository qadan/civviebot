'''
Autocomplete functions to let slash commands query the database.
'''

from typing import Type
from discord import AutocompleteContext
from sqlalchemy import select
from database.models import DeclarativeBase, Game, Player
from database.utils import get_session

def _yield_name_by_type(model: Type[DeclarativeBase], ctx: AutocompleteContext) -> str:
    with get_session() as session:
        for result in session.scalars(select(model).where(
                model.webhookurl.channelid == ctx.interaction.channel_id
                and model.name.like(f'%{ctx.value}%'))).all():
            yield result.name

def get_games_for_channel(ctx: AutocompleteContext) -> str:
    '''
    Autocomplete to return games in the context channel.
    '''
    yield _yield_name_by_type(Game, ctx)

def get_players_for_channel(ctx: AutocompleteContext) -> str:
    '''
    Autocomplete to return players in the context channel.
    '''
    yield _yield_name_by_type(Player, ctx)

def get_linked_players_for_channel(ctx: AutocompleteContext) -> str:
    '''
    Autocomplete to return players linked to the initiating user in the context channel.
    '''
    with get_session() as session:
        for result in session.scalars(select(Player).where(
            Player.discordid == ctx.interaction.user.id,
            Player.webhookurl.channelid == ctx.interaction.channel_id)).all():
            yield result.name
