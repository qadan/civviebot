'''
Connection management functionality for the CivvieBot database.
'''

from pony.orm.core import Database
from utils import config

def get_db() -> Database:
    '''
    Gets the Pony Database to use as the database for CivvieBot.
    '''
    database = Database()
    database.bind(**config.DATABASE_CONFIG)
    return database
