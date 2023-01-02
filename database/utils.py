'''
Connection management functionality for the CivvieBot database.
'''

from pony.orm.core import Database
from utils import config

def get_db() -> Database:
    '''
    Gets the correct Pony Database to use as the database for CivvieBot.
    '''
    database = Database()
    database.bind(provider='sqlite', filename=config.SQLITE_DATABASE, create_db=True)
    return database
