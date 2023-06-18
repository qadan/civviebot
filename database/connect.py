'''
Connection management functionality and base utilities for the database.
'''

import logging
from sqlalchemy import create_engine, URL, Engine
from sqlalchemy.orm import Session
from utils import config


logger = logging.getLogger(f'civviebot.{__name__}')


def get_db() -> Engine:
    '''
    Gets an Engine representing the CivvieBot database.
    '''
    url = URL.create(
        f'{config.CIVVIEBOT_DB_DIALECT}+{config.CIVVIEBOT_DB_DRIVER}',
        **config.DB_URL_KWARGS
    )
    return create_engine(url)


def get_session() -> Session:
    '''
    Gets a session for the CivvieBot database.
    '''
    return Session(get_db())
