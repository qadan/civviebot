'''
Connection management functionality for the CivvieBot database.
'''

from pony.orm.core import Database
from utils import config


def get_db():
    '''
    Gets the correct Pony Database to use as the database for CivvieBot.
    '''
    db_path = config.get_path('database')
    database = Database()
    database.bind(provider='sqlite', filename=db_path, create_db=True)
    return database
