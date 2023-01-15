'''
CivvieBot cog to handle commands dealing with one's own players.

Identical in functionality to the 'player' cog, but all of the commands only deal with the invoking
user.
'''

from discord import ApplicationContext
from discord.commands import SlashCommandGroup, option
from discord.ext.commands import Bot, Cog
from sqlalchemy import select
from bot.messaging import player as player_messaging
from database.autocomplete import (
    get_self_linked_players_for_channel,
    get_unlinked_players_for_channel)
from database.converters import PlayerConverter
from database.models import Player, WebhookURL
from database.utils import get_session
from utils import config, permissions

NAME = config.COMMAND_PREFIX + 'self'
DESCRIPTION = 'Manage your own user links and players in this channel.'

class SelfCommands(Cog, name=NAME, description=DESCRIPTION):
    '''
    Command group for dealing with one's own players and their links.
    '''

    def __init__(self, bot):
        '''
        Initialization; sets the bot.
        '''
        self.bot: Bot = bot

    selfcommands = SlashCommandGroup(NAME, DESCRIPTION)
    selfcommands.default_member_permissions = permissions.base_level

    @selfcommands.command(description='Link yourself to a player')
    @option(
        'player',
        input_type=PlayerConverter,
        description='The player to link yourself to',
        required=True,
        autocomplete=get_unlinked_players_for_channel)
    async def link(self, ctx: ApplicationContext, player: PlayerConverter):
        '''
        Links a player in the database to the initiating user.
        '''
        with get_session() as session:
            player = session.scalar(select(Player)
                .join(Player.webhookurl)
                .where(Player.name == player.name)
                .where(WebhookURL.channelid == ctx.channel_id))
            player.discordid = ctx.user.id
            session.commit()
            await ctx.respond(
                content=f"You've been linked to {player.name} and will be pinged on future turns.",
                ephemeral=True)

    @selfcommands.command(description="Remove a player's link to you")
    @option(
        'player',
        input_type=PlayerConverter,
        description='The player to unlink yourself from',
        required=True,
        autocomplete=get_self_linked_players_for_channel)
    async def unlink(self, ctx: ApplicationContext, player: PlayerConverter):
        '''
        Removes the link between a player in the database and its Discord ID.

        In practice, this is just setting the ID to an empty string.
        '''
        with get_session() as session:
            session.add(player)
            player.discordid = None
            session.commit()
            await ctx.respond(
                content=(f'You have removed the link between yourself and {player.name} and will '
                    'no longer be pinged directly on future turns.'),
                ephemeral=True)

    @selfcommands.command(
        description="Find which games associated with this channel you're part of")
    async def games(self, ctx: ApplicationContext):
        '''
        Responds with a list of games the given user is a part of in the channel they interacted in.
        '''
        await ctx.respond(
            embed=player_messaging.get_player_games_embed(ctx.channel_id, ctx.interaction.user),
            ephemeral=True)

    @selfcommands.command(description="Find out which games you're up in")
    async def upin(self, ctx: ApplicationContext):
        '''
        Responds with a list of games the user calling this command is a part of, and currently up
        in, in the channel they interacted in.
        '''
        await ctx.respond(
            embed=player_messaging.get_player_upin_embed(ctx.channel_id, ctx.user),
            ephemeral=True)

def setup(bot: Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(SelfCommands(bot))
