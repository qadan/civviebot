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
    logger.info(f'Connecting to civviebot database at {url.__to_string__()}')
    database = create_engine(url)
    return database


def get_session() -> Session:
    '''
    Gets a session for the CivvieBot database.
    '''
    return Session(get_db())
