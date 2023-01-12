'''
Interaction components to use with the 'notify' cog.
'''

import logging
from random import choice
from discord import ButtonStyle, Interaction
from bot.interactions.common import GameAwareButton, View
from database.models import Player
from database.utils import get_session
from utils.utils import get_discriminated_name

logger = logging.getLogger(f'civviebot.{__name__}')

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

    def set_attributes_from_game(self):
        '''
        Sets button attributes from properties in self.game.
        '''
        for key, val in self.get_attributes_from_game():
            setattr(self, key, val)

    def get_attributes_from_game(self):
        '''
        Returns an appropriate set of button attributes for the current value of self.game.
        '''
        if self.game.muted:
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
        with get_session() as session:
            session.add(self.game)
            self.game.muted = not self.game.muted
            session.commit()
            self.set_attributes_from_game()
            await interaction.response.edit_message(
                view=View(PlayerLinkButton(self.game.turns[0].player), self))
            await interaction.followup.send(
                self.muted if self.game.muted else self.unmuted,
                ephemeral=True)
            logger.info('User %s toggled notifications for game %s (now %s, tracked in %d)',
                get_discriminated_name(interaction.user),
                self.game.name,
                'muted' if self.game.muted else 'unmuted',
                interaction.channel_id)

class PlayerLinkButton(GameAwareButton):
    '''
    Button for toggling the link between a player and a Discord ID.
    '''

    def __init__(self, player: Player, *args, **kwargs):
        '''
        Initialization so we can hold the player.
        '''
        self._player = player
        super().__init__(*args, **kwargs)
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

    def set_attributes_from_player(self):
        '''
        Sets button attributes from properties in self.player.
        '''
        for key, val in self.get_attributes_from_player():
            setattr(self, key, val)

    def get_attributes_from_player(self):
        '''
        Returns an appropriate set of button attributes for the current value of self.player.
        '''
        if self.player.discordid:
            return (
                ('label', 'Unlink Player'),
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
        with get_session() as session:
            session.add(self.player)
            self.player.discordid = interaction.user.id if not self.player.discordid else None
            session.commit()
            self.set_attributes_from_player()
        await interaction.response.edit_message(
            view=View(self, MuteButton(self.game)))
        await interaction.followup.send(
            self.linked if self.player.discordid else self.unlinked,
            ephemeral=True)
        logger.info('User %s has %s player %s to themselves (channel: %d)',
            get_discriminated_name(interaction.user),
            'linked themselves to' if self.player.discordid else 'unlinked themselves from',
            self.player.name,
            interaction.channel_id)

    @property
    def player(self) -> Player:
        '''
        The player being referenced by this button.
        '''
        return self._player
