'''
Builders for portions of messages dealing with webhook URLs.
'''

from typing import List
from discord import Embed
from database.models import WebhookURL
from utils.utils import generate_url, expand_seconds_to_string


def get_info_embed(webhook_url: WebhookURL):
    '''
    Gets the embed for displaying information about a webhook URL.
    '''
    full_url = generate_url(webhook_url.slug)
    info = Embed(
        title=full_url,
        description='Games tracked using this webhook URL will use the following settings:')
    info.add_field(
        name='Notifies after:',
        value=f'{webhook_url.minturns} turns',
        inline=False)
    info.add_field(
        name='Re-ping frequency:',
        value=f'Every {expand_seconds_to_string(webhook_url.notifyinterval)}',
        inline=False)
    info.add_field(
        name='Games attached:',
        value=f'{len(webhook_url.games)} game{"s"[:len(webhook_url.games)^1]}',
        inline=False)
    info.set_footer(
        text=('To get a list of all active games attached to this URL, use "/c6url info" and set '
            f'the "webhook_url" to {webhook_url.slug}'))
    return info


def get_list_embed(webhook_urls: List[WebhookURL]):
    '''
    Gets the embed to use when displaying a list of all webhook URLs.
    '''
    whurl_list = Embed(title='All webhook URLs')
    def urlstring(url: WebhookURL):
        return f'{generate_url(url.slug)} ({len(url.games)} game{"s"[:len(url.games)^1]})'
    urls = '\n'.join([urlstring(url) for url in webhook_urls])
    if not urls:
        urls = ('There are no webhook URLs created in this channel. Use `/c6url new` to get one '
            'started.')
    else:
        whurl_list.add_field(name='URLs:', value=urls)
        whurl_list.set_footer(
            text=('To get a list of all active games attached to a URL, use "/c6url info" and set '
                'the "webhook_url" to the one you would like information about.'))
    return whurl_list
