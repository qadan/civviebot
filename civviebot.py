import config
import translator
from flask import Flask, request
from requests import post as post_request

app = Flask(__name__)
cb_config = config.CivvieBotConfig()
cb_translator = translator.CivvieBotTranslator(cb_config)

DEBUG = cb_config.get('debug_mode')

@app.route('/civviebot', methods=['POST'])
def process_request():
	'''
	Basic route. Accepts JSON from Civ VI, POSTs to Discord.
	'''
	translated_data = cb_translator.translate(request.get_json())
	response = post_request(cb_config.get('webhook_url'), json=translated_data)