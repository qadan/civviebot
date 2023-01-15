'''
API for receiving incoming requests from Civilization 6.
'''

from flask import Flask
from api.routes import api_blueprint
from database.utils import emit_all
from utils.config import initialize_logging

initialize_logging()
emit_all()
civviebot_api = Flask(__name__)
civviebot_api.register_blueprint(api_blueprint)
