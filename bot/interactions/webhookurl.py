'''
Interaction components to use with the 'webhookurl' cog.
'''

import logging
from typing import List
from discord import Interaction, SelectOption, ComponentType, ChannelType, TextChannel
from discord.ui import View
from discord.ext.commands import Bot
from pony.orm import db_session, TransactionIntegrityError, ObjectNotFound
import bot.messaging.webhookurl as whurl_messaging
from bot.interactions.common import (
    MinTurnsInput,
    NotifyIntervalInput,
    ChannelAwareModal,
    ChannelAwareSelect)
from database.models import WebhookURL
from utils.errors import ValueAccessError
from utils.utils import (
    VALID_CHANNEL_TYPES,
    generate_url,
    generate_slug,
    get_discriminated_name,
    handle_callback_errors,
    pluralize)


URL_SELECT_FAILED = ('An error occurred and CivvieBot was unable to get the selected webhook URL. '
    "Please try again later, and if this persists, contact CivvieBot's author.")


class SelectUrl(ChannelAwareSelect):
    '''
    Select drop-down for choosing a webhook URL in a channel.

    Uses custom_id 'select_url'.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor; maintains the URL slug.
        '''
        self._slug = None
        super().__init__(
            custom_id='select_url',
            placeholder='Select a URL',
            *args,
            **kwargs)
        self.options = self.get_url_options()
        if not self.options:
            raise ValueAccessError('No URLs found')


    @property
    def slug(self) -> str:
        '''
        Getter for the slug.
        '''
        if self._slug is None:
            try:
                slug = self.values[0]
            except IndexError as error:
                raise ValueAccessError('Attempting to access slug before it was set') from error
            if slug == '':
                raise ValueAccessError('Tried to access slug but it was empty')
        return slug


    @db_session
    def get_url_option(self, url: WebhookURL) -> SelectOption:
        '''
        Returns a webhook URL as a SelectOption.
        '''
        return SelectOption(
            label=generate_url(url.slug),
            value=url.slug,
            description=pluralize('active game', url.games))


    @db_session
    def get_url_options(self) -> List[SelectOption]:
        '''
        Returns a list of webhook URLs as SelectOptions.
        '''
        return [self.get_url_option(url) for url in
            WebhookURL.select(lambda whu: whu.channelid == self.channel_id)]


class WebhookUrlModal(ChannelAwareModal):
    '''
    Small abstraction for a modal that is aware of a webhook URL's slug.
    '''

    def __init__(self, slug: str, *args, **kwargs):
        '''
        Constructor; stores the slug.
        '''
        self._slug = slug
        super().__init__(*args, **kwargs)


    @property
    def slug(self):
        '''
        Getter for the slug.
        '''
        return self._slug


class TextChannelSelect(ChannelAwareSelect):
    '''
    Makes a select menu whose options are text channel types.

    Uses custom_id 'channel_select'.
    '''

    def __init__(self, channel_id: int, bot: Bot, *args, selected_channel: int = None, **kwargs):
        '''
        Constructor; establishes the channel property and sets the component type to channel_select.
        '''
        if selected_channel is not None:
            channel = bot.get_channel(selected_channel)
            if channel:
                self._selected_channel = channel
            else:
                logging.error('Attempting to get an inaccessible channel %d from channel %d',
                    selected_channel,
                    channel_id)
        else:
            self._selected_channel = None
        kwargs['select_type'] = ComponentType.channel_select
        kwargs['channel_types'] = VALID_CHANNEL_TYPES
        kwargs['custom_id'] = 'channel_select'
        super().__init__(channel_id, bot, *args, **kwargs)


    @property
    def selected_channel(self) -> TextChannel:
        '''
        The selected channel.
        '''
        if not self._selected_channel:
            try:
                self._selected_channel = self.bot.get_channel(int(self.values[0]))
            except IndexError as error:
                raise ValueAccessError('Attempting to access channel before it was set.') from error
            except ValueError as error:
                raise ValueAccessError(
                    'Tried to access channel but it cannot be cast to an integer.') from error
        return self._selected_channel

        
    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        new_channel_id = self.slug
        with db_session():
            whurl = WebhookURL[self.slug]
            whurl.channelid = new_channel_id
        logging.info('User %s has moved wehbhook URL from channel %d to %d',
            get_discriminated_name(interaction.user),
            self.channel_id,
            new_channel_id)
        new_channel = self.bot.get_channel(new_channel_id)
        await interaction.response.send_message(
            (f'The webhook URL {generate_url(self.slug)} has been moved to **{new_channel.name}**. '
                'Games that are tracked via this webhook URL will now send turn notifications to '
                'that channel.'),
            ephemeral=True)


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for moving a webhook URL.
        '''
        match error.__class__.__name__:
            case 'ObjectNotFound':
                await interaction.response.send_message(
                    ('Unable to move the given webhook URL as it no longer seems to exist. Was it '
                        'moved or deleted before you were able to move it?'),
                    ephemeral=True)
            case _:
                await super().on_error(error, interaction)


class NewWebhookModal(ChannelAwareModal):
    '''
    Modal for creating a new webhook.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor; sets the text fields.
        '''
        super().__init__(
            MinTurnsInput(),
            NotifyIntervalInput(),
            *args,
            **kwargs)


    async def callback(self, interaction: Interaction):
        '''
        Callback to create the URL from the given
        '''
        initiator = get_discriminated_name(interaction.user)
        min_turns = self.get_child_value(MinTurnsInput.custom_id)
        notify_interval = self.get_child_value(NotifyIntervalInput.custom_id)

        with db_session():
            try:
                slug = generate_slug()
                new_url = WebhookURL(
                    channelid=str(self.channel_id),
                    slug=slug,
                    minturns=min_turns,
                    notifyinterval=notify_interval)
            except TransactionIntegrityError:
                # Let's try some more before failing.
                logging.warning(
                    'Failed to create webhook URL with slug %s (integrity constraint violation)',
                    slug)
                for _ in range(0, 100):
                    try:
                        new_url = WebhookURL(
                            channelid=str(self.channel_id),
                            slug=generate_slug(),
                            minturns=min_turns,
                            notifyinterval=notify_interval)
                        break
                    except TransactionIntegrityError:
                        if _ == 100:
                            logging.error(
                                'Failed to create a webhook URL after 100 tries')
                            await interaction.response.send_message(
                                content=('Failed to create a webhook URL. Please try again, and if '
                                    'the issue persists, an administrator may need to contact the '
                                    'CivvieBot author on GitHub.'))
                            return

        url = generate_url(new_url.slug)
        logging.info('New URL: %s (generated by %s in channel %d)', url, initiator, self.channel_id)
        await interaction.response.send_message(f'Created a new Civilization 6 Webhook URL: {url}')


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for creating a webhook URL.
        '''
        match error.__class__.__name__:
            case 'ValueAccessError':
                logging.error(
                    'New URL creation failed due to input issues (initiated by %s in channel %d)',
                    get_discriminated_name(interaction.user),
                    self.channel_id)
                await interaction.response.send_message(
                    'An issue has occurred; the new Webhook URL was not created.',
                    ephemeral=True)
            case _:
                logging.error('An unexpected error occurred while creating a new Webhook URL: %s',
                    error.args[0])
                await interaction.response.send_message(
                    'An unexpected error occurred; the new Webhook URL was not created.',
                    ephemeral=True)


class EditUrlModal(WebhookUrlModal):
    '''
    Modal for editing the configuration of a webhook URL.
    '''

    def __init__(self, slug: str, channel_id: int, bot: Bot, *args, **kwargs):
        '''
        Constructor; establishes the modal with input children.
        '''
        with db_session():
            try:
                whurl = WebhookURL[slug]
                title = f'Editing Webhook URL .../{slug}'
                min_turns = whurl.minturns
                notify_interval = whurl.notifyinterval
            except ObjectNotFound:
                title = 'Webhook URL No Longer Exists'
                min_turns = None
                notify_interval = None
            if 'title' not in kwargs:
                kwargs['title'] = title
            super().__init__(
                slug,
                channel_id,
                bot,
                MinTurnsInput(min_turns=min_turns),
                NotifyIntervalInput(notify_interval=notify_interval),
                *args,
                **kwargs)


    async def callback(self, interaction: Interaction):
        '''
        Webhook URL edit callback.
        '''
        new_props = {
            ('channelid', self.get_child_value('channel_select')),
            ('minturns', self.get_child_value('min_turns')),
            ('notifyinterval', self.get_child_value('notify_interval')),
        }
        with db_session():
            webhook_url = WebhookURL[self.slug]
            for prop, new_val in new_props:
                setattr(webhook_url, prop, new_val)
        logging.info('Updated webhook URL %s', webhook_url.slug)
        await interaction.response.send_message(
            f'The webhook URL {webhook_url.slug} has been updated.')


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for the edit callback.
        '''
        match error.__class__.__name__:
            case 'ObjectNotFound':
                await interaction.response.send_message(
                    ('Unable to edit the given webhook URL as it no longer seems to exist. Was it '
                        'removed before you were able to edit it?'),
                    ephemeral=True)
            case 'ValueAccessError':
                await interaction.response.send_message(URL_SELECT_FAILED, ephemeral=True)
                super().on_error(error, interaction)


class SelectUrlForEdit(SelectUrl):
    '''
    Select URL menu that responds to interaction with an edit modal.
    '''

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Selection callback; responds with an EditUrlModal.
        '''
        await interaction.response.send_modal(EditUrlModal(self.slug, self.channel_id, self.bot))


class SelectUrlForMove(SelectUrl):
    '''
    Select URL menu that responds to interaction with a move modal.
    '''

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Selection callback; responds with a MoveUrlModal.
        '''
        await interaction.response.edit_message(
            content=f'Moving {generate_url(self.slug)} ...\nSelect a channel to move this URL to:',
            view=View(TextChannelSelect(self.channel_id, self.bot)))


class SelectUrlForDelete(SelectUrl):
    '''
    Select URL menu that response to an interaction with a delete confirmation modal.
    '''

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Deletion callback; sends the confirmation modal.
        '''
        await interaction.response.send_modal(DeleteUrlModal(self.slug, self.channel_id, self.bot))


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handling for the confirmation modal.
        '''
        await interaction.response.send_message(content=URL_SELECT_FAILED, ephemeral=True)
        if error.__class__.__name__ != 'ValueAccessError':
            logging.error('An unexpected error occurred while editing a Webhook URL: %s',
                error.args[0])


class DeleteUrlModal(WebhookUrlModal):
    '''
    Modal for confirmation of deleting the URL.
    '''

    async def callback(self, interaction: Interaction):
        '''
        Confirmation callback; deletes the URL.
        '''
        with db_session():
            webhook_url = WebhookURL[self.slug]
            webhook_url.delete()
        logging.info('Deleted webhook URL %s', webhook_url.slug)
        await interaction.response.send_message(
            f'The webhook URL {webhook_url.slug} has been deleted.',
            ephemeral=True)


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for the confirmation callback.
        '''
        match error.__class__.__name__:
            case 'ConstraintError':
                await interaction.response.send_message(
                    f'An error occurred and the webhook URL {self.slug} was not deleted',
                    ephemeral=True)
            case 'ObjectNotFound':
                await interaction.response.send_message(
                    'The given webhook URL could not be found. Was it already deleted?',
                    ephemeral=True)
            case _:
                await interaction.response.send_message(URL_SELECT_FAILED, ephemeral=True)
                super().on_error(error, interaction)


class SelectUrlForInfo(SelectUrl):
    '''
    Select menu whose callback provides the user info.
    '''

    def __init__(self, private: bool, *args, **kwargs):
        '''
        Constructor; establishes the 'private' property.
        '''
        self._private = private
        super().__init__(*args, **kwargs)


    @property
    def private(self) -> bool:
        '''
        Getter for the 'private' property.
        '''
        return self._private


    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback for sending info.
        '''
        with db_session():
            webhook_url = WebhookURL[self.slug]
            await interaction.response.send_message(
                embed=whurl_messaging.get_info_embed(webhook_url))
            logging.info('Provided information about URL %s to user %s in channel %d',
                webhook_url.slug,
                get_discriminated_name(interaction.user),
                self.channel_id)


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handling for sending info.
        '''
        match error.__class__.__name__:
            case 'ObjectNotFound':
                await interaction.response.send_message(
                    ('Failed to find the given webhook URL to get information about; was it '
                        'deleted before information could be provided?'),
                    ephemeral=True)
                return
            case 'BadArgument':
                await interaction.response.send_message(
                    'No such webhook URL is active in this channel')
                logging.error('Failed to provide information about URL %s to user %s in channel %d',
                    self.slug,
                    get_discriminated_name(interaction.user),
                    self.channel_id)
