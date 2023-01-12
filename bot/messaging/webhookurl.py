'''
Message builders for WebhookURLs.
'''

from discord import Embed
from database.models import WebhookURL
from utils import config
from utils.utils import expand_seconds_to_string, generate_url, pluralize

def get_webhookurl_info_embed(url: WebhookURL):
    '''
    Gets the embed to display information about a URL.
    '''
    full_url = generate_url(url.slug)
    info = Embed(
        title=full_url,
        description=('Games tracked using this webhook URL will default to the following '
            'settings:'))
    info.add_field(
        name='Notifies after:',
        value=f'Turn {url.minturns}',
        inline=False)
    re_pings = (f'Every {expand_seconds_to_string(url.remindinterval)}' if url.remindinterval
        else 'Does not re-ping')
    info.add_field(
        name='Re-ping frequency:',
        value=re_pings,
        inline=False)
    info.add_field(
        name='Games tracked by this URL:',
        value=pluralize("game", url.games),
        inline=False)
    info.set_footer(
        text=(f'To get more information about a game tracked in this channel, use '
            f'"/{config.COMMAND_PREFIX}game info"'))
    return info
