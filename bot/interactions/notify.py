'''
Interaction components to use with the 'notify' cog.
'''

import logging
from random import choice
from discord import ButtonStyle, Interaction
from discord.ui import View
from pony.orm import db_session, ObjectNotFound
from bot.interactions.common import GameAwareButton
from database import models
from utils.utils import get_discriminated_name


class MuteButton(GameAwareButton):
    '''
    Button for toggling a game as muted vs. unmuted.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Initialization so we can hold attributes about the game.
        '''
        super().__init__(*args, **kwargs)
        self.set_attributes_from_game()


    muted = 'Notifications for this game have been muted.'
    unmuted = 'Notifications for this game have been unmuted.'


    def set_attributes_from_game(self, game: models.Game = None):
        '''
        Sets button attributes from properties in self.game.
        '''
        for key, val in self.get_attributes_from_game(game):
            setattr(self, key, val)


    def get_attributes_from_game(self, game: models.Game = None):
        '''
        Returns an appropriate set of button attributes for the current value of self.game.
        '''
        if game is None:
            with db_session():
                try:
                    game = models.Game[self.game_id]
                except ObjectNotFound:
                    return (
                        ('label', 'Game no longer exists'),
                        ('emoji', '🚫'),
                        ('style', ButtonStyle.grey),
                        ('disabled', True))
        if game.muted:
            return (
                ('label', 'Unmute for all'),
                ('emoji', '🔊'),
                ('style', ButtonStyle.primary))
        return (
            ('label', 'Mute for all'),
            ('emoji', '🔇'),
            ('style', ButtonStyle.danger))


    async def callback(self, interaction: Interaction):
        '''
        Button clicking callback.

        Modifies the original response's view with an updated button, and informs the user.
        '''
        with db_session():
            game = models.Game[self.game_id]
            game.muted = not game.muted
            self.set_attributes_from_game(game)
            await interaction.response.edit_message(
                view=View(PlayerLinkButton(game.lastup.id, game.id), self))
            await interaction.followup.send(
                self.muted if game.muted else self.unmuted,
                ephemeral=True)
            logging.info('User %s toggled notifications for game %s (now %s, tracked in %d)',
                get_discriminated_name(interaction.user),
                game.gamename,
                'muted' if game.muted else 'unmuted',
                interaction.channel_id)


class PlayerLinkButton(GameAwareButton):
    '''
    Button for toggling the link between a player and a Discord ID.
    '''

    def __init__(self, player_id: int, game_id: int, *args, **kwargs):
        '''
        Initialization so we can hold the player.
        '''
        super().__init__(game_id, *args, **kwargs)
        self._player_id = player_id
        self.set_attributes_from_player()


    # When no link, pick an emoji from here.
    could_be_me = ['👶', '👩‍🎤', '🕵', '💂‍♀️', '🤴',
                   '👸', '👲', '🤵', '👼', '🎅',
                   '🤶', '🦸', '🦹', '🧙', '🧚',
                   '🧛‍♂️', '🧜‍♂️', '🧝‍♂️', '🤹', '🏄']
    # When there is a link, pick an emoji from here.
    is_not_me = ['🙅‍♀️', '🙅‍♂️']
    linked = "You've been linked to this player and will recieve future notifications"
    unlinked = "You've been unlinked from this player and will stop recieving future notifications"


    def set_attributes_from_player(self, player: models.Player = None):
        '''
        Sets button attributes from properties in self.player.
        '''
        for key, val in self.get_attributes_from_player(player):
            setattr(self, key, val)


    def get_attributes_from_player(self, player: models.Player = None):
        '''
        Returns an appropriate set of button attributes for the current value of self.player.
        '''
        if player is None:
            with db_session():
                try:
                    player = models.Player[self.player_id]
                except ObjectNotFound:
                    return (
                        ('label', 'Player no longer exists'),
                        ('emoji', '🚫'),
                        ('style', ButtonStyle.grey),
                        ('disabled', True))
        if player.discordid != '':
            return (
                ('label', 'Unlink me'),
                ('emoji', choice(self.is_not_me)),
                ('style', ButtonStyle.danger))
        return (
            ('label', 'This is me'),
            ('emoji', choice(self.could_be_me)),
            ('style', ButtonStyle.primary))


    async def callback(self, interaction: Interaction):
        '''
        Button clicking callback.

        Modifies the original response's view with an updated button, and informs the user.
        '''
        with db_session():
            player = models.Player[self.player_id]
            player.discordid = str(interaction.user.id) if not player.discordid else ''
            self.set_attributes_from_player(player)
        await interaction.response.edit_message(
            view=View(self, MuteButton(self.game_id)))
        await interaction.followup.send(
            self.linked if player.discordid else self.unlinked,
            ephemeral=True)
        logging.info('User %s has %s player %s to themselves (channel: %d)',
            get_discriminated_name(interaction.user),
            'linked themselves to' if player.discordid else 'unlinked themselves from',
            player.playername,
            interaction.channel_id)


    @property
    def player_id(self):
        '''
        ID of the player being referenced by this button.
        '''
        return self._player_id
