'''
Slash command option converters for database items.
'''

from typing import Type
from discord import ApplicationContext
from discord.ext.commands import Converter
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from database.models import Game, Player, CivvieBotBase, WebhookURL
from database.utils import get_session

class UnitConverter(Converter):
    '''
    Base class to convert a string to a unit in the database.
    '''

    _unit_type: CivvieBotBase

    async def convert(self, ctx: ApplicationContext, arg: str):
        '''
        Converts the given string to the appropriate Game.
        '''
        with get_session() as session:
            game = session.scalar(select(self.unit_type)
                .join(self.unit_type.webhookurl)
                .where(self.unit_type.name == arg)
                .where(WebhookURL.channelid == ctx.channel_id))
        if not game:
            raise NoResultFound('Failed to find the given resource in the database.')
        return game

    @property
    def unit_type(self) -> Type[CivvieBotBase]:
        '''
        The type of unit in the database this should convert to.
        '''
        return self._unit_type

class GameConverter(UnitConverter):
    '''
    Converts a string game name into a Game.
    '''
    _unit_type = Game

class PlayerConverter(UnitConverter):
    '''
    Converts a string player name into a Player.
    '''
    _unit_type = Player
