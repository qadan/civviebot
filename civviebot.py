from utils.config import CivvieBotConfig
from utils.translator import CivvieBotTranslator
from flask import Flask, request, jsonify
from requests import post as post_request

civviebot = Flask(__name__)
cb_config = CivvieBotConfig()
cb_translator = CivvieBotTranslator(cb_config)

DEBUG = cb_config.get('debug_mode')
civviebot.config.from_object(__NAME__)


@civviebot.route('/civviebot', methods=['POST'])
def process_request():
    '''
    Basic route. Accepts JSON from Civ VI, POSTs to Discord.
    '''
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
