'''
Interactions intended to work with the 'base' cog.
'''

import logging
from os import listdir, path
from discord import Interaction, Embed
from discord.ui import Select
from utils import config
from utils.errors import ValueAccessError
from utils.utils import get_discriminated_name, handle_callback_errors

logger = logging.getLogger(f'civviebot.{__name__}')

class FaqQuestionSelect(Select):
    '''
    Select menu to pick an FAQ question.
    '''

    def __init__(self, *args, faq_md_path: str = None, **kwargs):
        '''
        Constructor; sets the list of options.
        '''
        if 'placeholder' not in kwargs:
            kwargs['placeholder'] = 'Pick a topic'
        super().__init__(*args, **kwargs)
        if faq_md_path is None:
            faq_md_path = path.join(path.dirname(path.realpath(__file__)), 'markdown', 'faq')
        self._faq_md_path = faq_md_path
        self._faq = None
        faqs = sorted(listdir(faq_md_path))
        for faq in faqs:
            with open(path.join(faq_md_path, faq), 'r', encoding='utf-8') as file:
                title = file.readline()
                self.add_option(label=title, value=faq)

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback; sets the markdown embed.
        '''
        with open(path.join(self.faq_md_path, self.faq), 'r', encoding='utf-8') as faq:
            title = faq.readline().strip('_*')
            embed = Embed(title=title)
            embed.description = faq.read().replace('%COMMAND_PREFIX%', config.get('command_prefix'))
            await interaction.response.edit_message(content='', embed=embed)
            logger.info(
                'User %s requested FAQ documentation %s (%s) in channel %d',
                get_discriminated_name(interaction.user),
                title,
                self.faq,
                interaction.channel_id)

    @property
    def faq_md_path(self):
        '''
        The path to the FAQ markdown files.
        '''
        return self._faq_md_path

    @property
    def faq(self):
        '''
        The full path to the selected faq.
        '''
        try:
            self._faq = self.values[0]
        except IndexError as error:
            raise ValueAccessError('Attempting to access faq before it was set') from error
        except ValueError as error:
            raise ValueAccessError(
                'Tried to access faq but it cannot be cast to an integer') from error
        return self._faq
