'''
Interaction components to use with the 'notify' cog.
'''

from random import choice
from discord import ButtonStyle, Interaction
from discord.ui import View, Button
from pony.orm import db_session
from database import models


class MuteButton(Button):
    '''
    Button for toggling a game as muted vs. unmuted.
    '''

    def __init__(self, game: dict):
        '''
        Initialization so we can hold attributes about the game.
        '''
        super().__init__()
        self.game = game
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
        if self.game.get('muted', models.Game.muted.default):
            return (
                ('label', 'Unmute for all'),
                ('emoji', '🔊'),
                ('style', ButtonStyle.primary),
            )
        return (
            ('label', 'Mute for all'),
            ('emoji', '🔇'),
            ('style', ButtonStyle.danger),
        )


    async def callback(self, interaction: Interaction):
        '''
        Button clicking callback.

        Modifies the original response's view with an updated button, and informs the user.
        '''
        with db_session():
            webhook = models.WebhookURL.get(
                channelid=str(interaction.channel_id))
            game = models.Game.get(webhookurl=webhook)
            game.muted = not game.muted
            self.game = game.to_dict()
            self.set_attributes_from_game()
            last_up = game.lastup.to_dict()
        await interaction.response.edit_message(
            view=View(PlayerLinkButton(last_up), self))
        await interaction.followup.send(
            self.muted if game.muted else self.unmuted,
            ephemeral=True)


class PlayerLinkButton(Button):
    '''
    Button for toggling the link between a player and a Discord ID.
    '''

    def __init__(self, player: dict):
        '''
        Initialization so we can hold attributes about the player.
        '''
        super().__init__()
        self.player = player
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
        if self.player.get('discordid', models.Player.discordid.default):
            return (
                ('label', 'Unlink me'),
                ('emoji', choice(self.is_not_me)),
                ('style', ButtonStyle.danger),
            )
        return (
            ('label', 'This is me'),
            ('emoji', choice(self.could_be_me)),
            ('style', ButtonStyle.primary),
        )


    async def callback(self, interaction: Interaction):
        '''
        Button clicking callback.

        Modifies the original response's view with an updated button, and informs the user.
        '''
        with db_session():
            webhook = models.WebhookURL.get(
                channelid=str(interaction.channel_id))
            game = models.Game.get(webhookurl=webhook)
            player = models.Player.get(lambda p: game in p.games)
            player.discordid = str(
                interaction.user.id) if not player.discordid else ''
            self.player = player.to_dict()
            self.set_attributes_from_player()
        await interaction.response.edit_message(
            view=View(self, MuteButton(game.to_dict())))
        await interaction.followup.send(
            self.linked if player.discordid else self.unlinked,
            ephemeral=True)
