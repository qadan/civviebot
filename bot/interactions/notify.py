'''
Interaction components to use with the 'notify' cog.
'''

import logging
from random import choice
from discord import ButtonStyle, Interaction
from sqlalchemy import select
from bot.interactions.common import GameAwareButton, View
from database.models import Player, Game, WebhookURL
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

    def set_attributes_from_game(self, muted: bool = None):
        '''
        Sets button attributes from properties in self.game.
        '''
        for key, val in self.get_attributes_from_game(muted):
            setattr(self, key, val)

    def get_attributes_from_game(self, muted: bool = None):
        '''
        Returns an appropriate set of button attributes for the current value of self.game.
        '''
        if muted is None:
            with get_session() as session:
                muted = session.scalar(select(Game.muted)
                    .join(Game.webhookurl)
                    .where(WebhookURL.channelid == self.channel_id)
                    .where(Game.name == self.game))
        if muted:
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
            game = session.scalar(select(Game)
                .join(Game.webhookurl)
                .where(WebhookURL.channelid == self.channel_id)
                .where(Game.name == self.game))
            game.muted = not game.muted
            session.commit()
            self.set_attributes_from_game(game.muted)
            await interaction.response.edit_message(
                view=View(PlayerLinkButton(game), self))
            await interaction.followup.send(
                self.muted if game.muted else self.unmuted,
                ephemeral=True)
            logger.info('User %s toggled notifications for game %s (now %s, tracked in %d)',
                get_discriminated_name(interaction.user),
                game.name,
                'muted' if game.muted else 'unmuted',
                interaction.channel_id)

class PlayerLinkButton(GameAwareButton):
    '''
    Button for toggling the link between a player and a Discord ID.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Initialization so we can hold the player.
        '''
        self._player = args[0].turns[0].player.name
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
    unlinked = "You've unlinked this player; they will stop recieving future notifications"

    def set_attributes_from_player(self, discordid: int = None):
        '''
        Sets button attributes from properties in self.player.
        '''
        for key, val in self.get_attributes_from_player(discordid):
            setattr(self, key, val)

    def get_attributes_from_player(self, discordid: int = None):
        '''
        Returns an appropriate set of button attributes for the current value of self.player.
        '''
        if not discordid:
            with get_session() as session:
                discordid = session.scalar(select(Player.discordid)
                    .join(Player.webhookurl)
                    .where(Player.name == self.player)
                    .where(WebhookURL.channelid == self.channel_id))
        if discordid:
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
            player = session.scalar(select(Player)
                .join(Player.webhookurl)
                .where(Player.name == self.player)
                .where(WebhookURL.channelid == self.channel_id))
            game = session.scalar(select(Game)
                .join(Game.webhookurl)
                .where(Game.name == self.game)
                .where(WebhookURL.channelid == self.channel_id))
            player.discordid = None if player.discordid else interaction.user.id
            session.commit()
            self.set_attributes_from_player(player.discordid)
            await interaction.response.edit_message(
                view=View(self, MuteButton(game)))
            await interaction.followup.send(
                self.linked if player.discordid else self.unlinked,
                ephemeral=True)
            logger.info('User %s has %s player %s (channel: %d)',
                get_discriminated_name(interaction.user),
                'linked themselves to' if player.discordid else 'removed the link from',
                player.name,
                interaction.channel_id)

    @property
    def player(self) -> str:
        '''
        The player being referenced by this button.
        '''
        return self._player
