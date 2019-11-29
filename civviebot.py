from utils.config import CivvieBotConfig
from utils.translator import CivvieBotTranslator
from flask import Flask, Response, request, jsonify
from os import path
from requests import post as post_request

# Pre-config of the app.
cb_config = CivvieBotConfig()
cb_translator = CivvieBotTranslator(cb_config)

# Rest of the config.
DEBUG = cb_config.get('debug_mode')
civviebot = Flask(__name__)
civviebot.config.from_object(__name__)


@civviebot.route('/civviebot', methods=['GET', 'POST'])
def process_request():
    '''
    Basic route. Accepts JSON from Civ VI, POSTs to Discord.
    '''
    if request.method == 'POST':
        civ_data = cb_translator.map(request.get_json())
        if int(civ_data['turn']) >= cb_config.get('minimum_turn'):
            response = post_request(
                    cb_config.get('webhook_url'),
                    json=cb_translator.get_discord_webhook_json(civ_data))
            return jsonify({
                'sent': True,
                'data': civ_data,
                })

        return jsonify({
            'sent': False,
            'data': civ_data,
            })
    else:
        # Allow someone to ping the server and confirm it's up and running.
        with open(path.dirname(path.realpath(__file__)) + '/ping.json', 'r') as info:
            return Response(info.read(), mimetype='application/json')
