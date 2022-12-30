'''
Interaction components to use with the 'webhookurl' cog.
'''

import logging
from traceback import extract_tb, format_list
from typing import List
from discord import Interaction, SelectOption, ComponentType, TextChannel, Embed
from discord.ui import Button
from discord.ext.commands import Bot
from pony.orm import db_session, TransactionIntegrityError, ObjectNotFound
from bot.cogs.game import NAME as game_name
from bot.interactions.common import (
    CancelButton,
    MinTurnsInput,
    NotifyIntervalInput,
    ChannelAwareModal,
    ChannelAwareSelect,
    View)
from database.models import WebhookURL
from utils.errors import ValueAccessError
from utils.utils import (
    VALID_CHANNEL_TYPES,
    expand_seconds_to_string,
    generate_url,
    generate_slug,
    get_discriminated_name,
    handle_callback_errors,
    pluralize)

logger = logging.getLogger(f'civviebot.{__name__}')

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


class TextChannelSelect(ChannelAwareSelect):
    '''
    Makes a select menu whose options are text channel types.

    Uses custom_id 'channel_select'.
    '''

    def __init__(
        self,
        slug: str,
        channel_id: int,
        bot: Bot,
        *args,
        selected_channel: int = None,
        **kwargs):
        '''
        Constructor; establishes the channel property and sets the component type to channel_select.
        '''
        self._slug = slug
        if selected_channel is not None:
            channel = bot.get_channel(selected_channel)
            if channel:
                self._selected_channel = channel
            else:
                logger.error('Attempting to get an inaccessible channel %d from channel %d',
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
        try:
            self._selected_channel = self.values[0]
        except IndexError as error:
            raise ValueAccessError('Attempting to access channel before it was set.') from error
        except ValueError as error:
            raise ValueAccessError(
                'Tried to access channel but it cannot be cast to an integer.') from error
        if not self._selected_channel:
            raise ValueAccessError('Failed to get the selected channel.')
        return self._selected_channel


    @property
    def slug(self):
        '''
        The slug of the webhook URL being moved.
        '''
        return self._slug


    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        with db_session():
            whurl = WebhookURL[self.slug]
            whurl.channelid = str(self.selected_channel.id)
        logger.info('User %s has moved wehbhook URL from channel %d to %d',
            get_discriminated_name(interaction.user),
            self.channel_id,
            self.selected_channel.id)
        await interaction.response.edit_message(
            content=(f'{generate_url(self.slug)} has been moved to <#{self.selected_channel.id}>. '
                'Games that are tracked via this webhook URL will now send turn notifications to '
                'that channel.'),
            view=None)


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for moving a webhook URL.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content=('Unable to move the given webhook URL as it no longer seems to exist. '
                    'Was it moved or deleted before you were able to move it?'),
                view=None)
            return
        await super().on_error(error, interaction)


class NewWebhookModal(ChannelAwareModal):
    '''
    Modal for creating a new webhook.
    '''

    def __init__(self, channel_id: int, bot: Bot, *args, **kwargs):
        '''
        Constructor; sets the text fields.
        '''
        super().__init__(
            channel_id,
            bot,
            MinTurnsInput(),
            NotifyIntervalInput(),
            *args,
            **kwargs)


    async def callback(self, interaction: Interaction):
        '''
        Callback to create the URL from the given
        '''
        initiator = get_discriminated_name(interaction.user)
        min_turns = self.get_child_value('min_turns')
        notify_interval = self.get_child_value('notify_interval')
        if notify_interval == 0:
            notify_interval = None

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
                logger.warning(
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
                            logger.error(
                                'Failed to create a webhook URL after 100 tries')
                            await interaction.response.send_message(
                                content=('Failed to create a webhook URL. Please try again, and if '
                                    'the issue persists, an administrator may need to contact the '
                                    'CivvieBot author on GitHub.'))
                            return

        url = generate_url(new_url.slug)
        logger.info('New URL: %s (generated by %s in channel %d)', url, initiator, self.channel_id)
        await interaction.response.send_message(f'Created a new Civilization 6 Webhook URL: {url}')


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for creating a webhook URL.
        '''
        if isinstance(error, ValueAccessError):
            logger.error(
                'New URL creation failed due to input issues (initiated by %s in channel %d)',
                get_discriminated_name(interaction.user),
                self.channel_id)
            await interaction.response.send_message(
                'An issue has occurred; the new Webhook URL was not created.',
                ephemeral=True)
            return
        if isinstance(error, ValueError):
            await interaction.response.send_message(
                ('Sorry, an issue occurred while trying to create this webhook URL. Make sure that '
                    'you fill in both fields with only numbers.'),
                ephemeral=True)
            return
        await super().on_error(error, interaction)


class EditUrlModal(ChannelAwareModal):
    '''
    Modal for editing the configuration of a webhook URL.
    '''

    def __init__(self, slug: str, channel_id: int, bot: Bot, *args, **kwargs):
        '''
        Constructor; establishes the modal with input children.
        '''
        self._slug = slug
        with db_session():
            try:
                whurl = WebhookURL[slug]
                title = f'Editing Webhook URL .../{slug}'
                min_turns = whurl.minturns
                notify_interval = whurl.notifyinterval if whurl.notifyinterval else 0
            except ObjectNotFound:
                title = 'Webhook URL No Longer Exists'
                min_turns = None
                notify_interval = None
            if 'title' not in kwargs:
                kwargs['title'] = title
            super().__init__(
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
        with db_session():
            webhook_url = WebhookURL[self.slug]
            minturns = self.get_child_value('min_turns')
            if minturns == 0:
                minturns = None
            webhook_url.notifyinterval = self.get_child_value('notify_interval')
        logger.info('Updated webhook URL %s', webhook_url.slug)
        await interaction.response.edit_message(
            content=f'The webhook URL {webhook_url.slug} has been updated.',
            embed=SelectUrlForInfo.get_embed(webhook_url),
            view=None)


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for the edit callback.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content=('Unable to edit the given webhook URL as it no longer seems to exist. Was '
                    'it removed before you were able to edit it?'),
                view=None)
            return
        if isinstance(error, ValueAccessError):
            logger.error(
                'URL edit failed due to input issues (initiated by %s in channel %d)',
                get_discriminated_name(interaction.user),
                self.channel_id)
            await interaction.response.edit_message(
                content='An issue has occurred; the Webhook URL was not modified.',
                view=None)
            return
        if isinstance(error, ValueError):
            await interaction.response.edit_message(
                content=('Sorry, an issue occurred while trying to edit this webhook URL. Make '
                    'sure that you fill in both fields with only numbers.'),
                view=None)
            return
        await super().on_error(error, interaction)


    @property
    def slug(self):
        '''
        Getter for the slug.
        '''
        return self._slug


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
            view=View(TextChannelSelect(self.slug, self.channel_id, self.bot)))


class SelectUrlForDelete(SelectUrl):
    '''
    Select URL menu that response to an interaction with a delete confirmation modal.
    '''

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Deletion callback; sends the confirmation modal.
        '''
        with db_session():
            url = WebhookURL[self.slug]
        await interaction.response.edit_message(
            content=f'Are you sure you want to delete {generate_url(url.slug)}?',
            embed=SelectUrlForInfo.get_embed(url),
            view=View(CancelButton(), ConfirmDeleteUrlButton()))


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handling for the confirmation modal.
        '''
        if isinstance(error, ValueAccessError):
            await interaction.response.edit_message(content=URL_SELECT_FAILED)
            logger.error('An unexpected error occurred while editing a Webhook URL: %s',
                error.args[0])
            return
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content='Failed to find the URL you selected; was it already deleted?')
            return
        await super().on_error(error, interaction)


class ConfirmDeleteUrlButton(Button):
    '''
    Button to assert that the given webhook URL should be deleted.
    '''

    def __init__(self, slug: str, *args, **kwargs):
        '''
        Constructor; stashes a URL slug.
        '''
        self._slug = slug
        super().__init__(*args, **kwargs)


    @property
    def slug(self) -> str:
        '''
        The slug of the URL being deleted.
        '''
        return self._slug


    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback; handles deleting the URL.
        '''
        with db_session():
            WebhookURL[self.slug].delete()
        await interaction.response.edit_message(
            content=(f'The webhook URL {generate_url(self.slug)} has been deleted. Games tracked '
            'by this URL have also been deleted.'))


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handling, especially if the URL wasn't found.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content='Failed to find the URL you selected; was it already deleted?')
            return
        logger.error(
            'Unexpected failure in ConfirmDeleteUrlButton: %s: %s\n%s',
            error.__class__.__name__,
            error,
            ''.join(format_list(extract_tb(error.__traceback__))))
        await interaction.response.edit_message(
            content=('An unknown error occurred; contact an administrator if this persists.'))


class SelectUrlForInfo(SelectUrl):
    '''
    Select menu whose callback provides the user info.
    '''


    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        '''
        Callback for sending info.
        '''
        with db_session():
            webhook_url = WebhookURL[self.slug]            
            await interaction.response.edit_message(content='', embed=self.get_embed(webhook_url))
        logger.info('Provided information about URL %s to user %s in channel %d',
            webhook_url.slug,
            get_discriminated_name(interaction.user),
            self.channel_id)


    @staticmethod
    @db_session
    def get_embed(url: WebhookURL):
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
        re_pings = (f'Every {expand_seconds_to_string(url.notifyinterval)}' if url.notifyinterval
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
                f'"/{game_name} info"'))
        return info


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handling for sending info.
        '''
        if isinstance(error, ObjectNotFound):
            await interaction.response.edit_message(
                content=('Failed to find the given webhook URL to get information about; was '
                    'it deleted before information could be provided?'))
            return
        await super().on_error(error, interaction)
