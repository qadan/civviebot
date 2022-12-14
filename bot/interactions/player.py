'''
Interaction components to use with the 'player' cog.
'''

import logging
from typing import List
from discord import ComponentType, Interaction, User
from discord.components import SelectOption
from discord.ext.commands import Bot
from pony.orm import db_session, left_join
from bot.interactions.common import ChannelAwareSelect, ChannelAwareModal
from bot.messaging import player as player_messaging
from database.models import Player
from utils.errors import ValueAccessError
from utils.utils import get_discriminated_name, handle_callback_errors, pluralize


SELECT_FAILED = ('An error occurred and CivvieBot was unable to get the selected option(s). '
    "Please try again later, and if this persists, contact CivvieBot's author.")


class UserSelect(ChannelAwareSelect):
    '''
    Helper for making a select menu with the 'user_select' component type; guess py-cord really
    wants you to use those decorators because they're the only shortcut.

    Uses custom_id 'user_select'.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor; establishes the user property and sets the component type to user_select.
        '''
        self._user = None
        kwargs['select_type'] = ComponentType.user_select
        super().__init__(custom_id='user_select', *args, **kwargs)


    @property
    def user(self) -> User:
        '''
        The selected user.
        '''
        if not self._user:
            try:
                self._user = self.bot.get_user(int(self.values[0]))
            except IndexError as error:
                raise ValueAccessError('Attempting to access user before it was set.') from error
            except ValueError as error:
                raise ValueAccessError(
                    'Tried to access user but it cannot be cast to an integer.') from error
        return self._user


class PlayerSelect(ChannelAwareSelect):
    '''
    Select menu for choosing a player being tracked in a given channel.

    Uses custom_id 'player_select'.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor; establishes the player information.
        '''
        self._player_id = None
        super().__init__(
            custom_id='player_select',
            placeholder='Select a player',
            options=self.get_player_options(),
            *args,
            **kwargs)


    @db_session
    def get_player_as_option(self, player: Player) -> SelectOption:
        '''
        Returns a Player formatted as a SelectOption.
        '''
        return SelectOption(
            label=player.playername,
            value=str(player.id),
            description=(f'In {len(player.games)} {pluralize("game", player.games)} (up in '
                f'{len(player.upin)})'))


    @db_session
    def get_player_options(self) -> List[SelectOption]:
        '''
        Gets a List containing the Players in this channel as SelectOptions
        '''
        results = left_join(((p, g) for p in Player for g in p.games if
            g.webhookurl.channelid == self.channel_id))
        return [self.get_player_as_option(player) for player in results]


    @property
    def player_id(self) -> int:
        '''
        Getter for the player. Attempts to get the player ID from self.values.
        '''
        if not self._player_id:
            try:
                self._player_id = int(self.values[0])
            except IndexError as error:
                raise ValueAccessError('Attempting to access player before it was set.') from error
            except ValueError as error:
                raise ValueAccessError(
                    'Tried to access player but it cannot be cast to an integer.') from error
        return self._player_id



class LinkedPlayerSelect(PlayerSelect):
    '''
    Select menu for choosing a player in a given channel that is currently linked to a user.
    '''

    @db_session
    def get_player_as_option(self, player: Player) -> SelectOption:
        try:
            user = self.bot.get_user(int(player.discordid))
            if user:
                desc = f'Linked to {get_discriminated_name(user)}'
            else:
                desc = 'Unable to load linked user'
        except ValueError:
            desc = 'No longer appears to be linked'
        return SelectOption(
            label=player.playername,
            value=str(player.id),
            description=desc)


    @db_session
    def get_player_options(self) -> List[SelectOption]:
        '''
        Gets all players currently linked to a user in this channel as SelectOptions
        '''
        results = left_join(((p, g) for p in Player for g in p.games if
            g.webhookurl.channelid == self.channel_id and
            p.discordid != ''))
        return [self.get_player_as_option(result) for result in results]


class UnlinkedPlayerSelect(PlayerSelect):
    '''
    Select menu for choosing a player who is not currently linked to a user.
    '''

    @db_session
    def get_player_options(self) -> List[SelectOption]:
        '''
        Gets all players currently not linked to a user in this channel as SelectOptions
        '''
        results = left_join(((p, g) for p in Player for g in p.games if
            g.webhookurl.channelid == self.channel_id and
            p.discordid == ''))
        return [self.get_player_as_option(result) for result in results]


class LinkPlayerModal(ChannelAwareModal):
    '''
    Modal for linking a currently unlinked player to a user.
    '''

    def __init__(self, channel_id: int, bot: Bot, *args, **kwargs):
        '''
        Constructor; sets the select fields.
        '''
        self._bot = bot
        self._channel_id = channel_id
        super().__init__(
            UnlinkedPlayerSelect(channel_id=self.channel_id),
            UserSelect(channel_id=self.channel_id),
            *args,
            **kwargs)


    async def callback(self, interaction: Interaction):
        '''
        Submit handler for the modal; links the player and the user given.
        '''
        user = getattr(next(filter(lambda c: c.custom_id == 'user_select', self.children)), 'user')

        with db_session():
            player_id = getattr(
                next(filter(lambda c: c.custom_id == 'player_select', self.children)),
                'player_id')
            player = Player[player_id]
            player.discordid = user.id
            logging.info(
                'Set the Discord ID of %s (%d) to %d (channel: %d)',
                player.playername,
                player.id,
                user.id,
                interaction.channel_id)


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for player/user link.
        '''
        match error.__class__.__name__:
            case 'ValueAccessError':
                await interaction.response.send_message(SELECT_FAILED, ephemeral=True)
            case 'ObjectNotFound':
                await interaction.response.send_message(
                    ('Failed to find the selected player; was it removed before the link could be '
                        'created?'),
                    ephemeral=True)
            case _:
                await interaction.response.send_message(SELECT_FAILED, ephemeral=True)
                super().on_error(error, interaction)


    @property
    def channel_id(self) -> int:
        '''
        Getter for the channel_id.
        '''
        return self._channel_id

    @channel_id.setter
    def channel_id(self, value: int):
        '''
        Setter for the channel_id.
        '''
        self._channel_id = value
        self.children = [
            UnlinkedPlayerSelect(
                channel_id=self.channel_id,
                bot=self.bot),
            UserSelect(
                channel_id=self.channel_id,
                bot=self.bot)]


    @property
    def bot(self) -> Bot:
        '''
        Getter for the channel_id.
        '''
        return self._bot


class UnlinkPlayerSelect(LinkedPlayerSelect):
    '''
    Class containing callback to remove the user link from the given player.
    '''

    @handle_callback_errors
    async def callback(self, interaction: Interaction):
        with db_session():
            player = Player[self.player_id]
            existing_user = player.discordid
            player.discordid = ''

        logging.info(
            'Removed the link between player %s (%d) and Discord ID %s',
            player.name,
            player.value,
            existing_user)
        await interaction.response.send_message(
            f'The link between player {player.name} and its Discord user has been removed.')


    async def on_error(self, error: Exception, interaction: Interaction):
        '''
        Error handler for player link removal.
        '''
        match error.__class__.__name__:
            case 'ValueAccessError' | 'IndexError':
                await interaction.response.send_message(SELECT_FAILED, ephemeral=True)
            case 'ObjectNotFound':
                await interaction.response.send_message(
                    ('Unable to remove the link from this player as this player does not have a '
                        'link. Was it already removed?'),
                    ephemeral=True)
            case _:
                await interaction.response.send_message(SELECT_FAILED, ephemeral=True)


class UserLinkedPlayersSelect(PlayerSelect):
    '''
    Provides a drop-down menu to select one or more linked players.
    '''

    def __init__(self, user: User, *args, **kwargs):
        self._player_ids = None
        self._user = user
        del kwargs['user']
        kwargs['max_values'] = 25
        super().__init__(*args, **kwargs)


    @db_session
    def get_player_options(self) -> List[SelectOption]:
        '''
        Gets a List containing the Players in this channel as SelectOptions
        '''
        results = left_join(((p, g) for p in Player for g in p.games if
            g.webhookurl.channelid == self.channel_id and
            p.discordid == str(self.user.id)))
        return [self.get_player_as_option(player) for player in results]


    @property
    def user(self) -> User:
        '''
        Getter for the user.
        '''
        return self._user


class UnlinkUserModal(ChannelAwareModal):
    '''
    Provides a modal that allows for multi-select unlinking of a user's player links.
    '''

    def __init__(self, user: User, *args, **kwargs):
        '''
        Constructor; adds in the UserLinkedPlayersSelect.
        '''
        del kwargs['user']
        super().__init__(
            UserLinkedPlayersSelect(
                channel_id=kwargs['channel_id'],
                bot=kwargs['bot'],
                user=user),
            *args,
            **kwargs)


    async def callback(self, interaction: Interaction):
        '''
        Interaction callback; removes the links from the selected players.
        '''
        results = set()
        users = self.get_child_value('user_select')
        with db_session():
            for user_id in users:
                for player in left_join((p, g) for p in player for g in p.games if
                    p.discordid == user_id and g.webhookurl.channelid == self.channel_id):
                    player.discordid = ''
                    logging.info(
                        'Removed the link between player %s (%d) and Discord ID %d',
                        player.playername,
                        player.id,
                        user_id)
                    results.add((
                        player.playername,
                        f'Link removed from {get_discriminated_name(user_id)}'))
        await interaction.response.send_message(
            embed=player_messaging.get_user_unlink_embed(results))
