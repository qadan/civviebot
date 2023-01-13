'''
CivvieBot cog to handle commands dealing with players.
'''

from discord import ApplicationContext, SlashCommandOptionType, User
from discord.commands import SlashCommandGroup, option
from discord.ext.commands import Cog, Bot
from sqlalchemy import select
from bot.messaging import player as player_messaging
from database.autocomplete import get_linked_players_for_channel, get_players_for_channel, get_unlinked_players_for_channel
from database.converters import PlayerConverter
from database.models import Player, WebhookURL
from database.utils import get_session
from utils import config, permissions

NAME = config.COMMAND_PREFIX + 'player'
DESCRIPTION = 'Manage known players and user links in this channel.'

class PlayerCommands(Cog, name=NAME, description=DESCRIPTION):
    '''
    Command group for dealing with players in the database, and linking them to Discord users.
    '''

    def __init__(self, bot):
        '''
        Initialization; sets the bot.
        '''
        self.bot: Bot = bot

    players = SlashCommandGroup(NAME, DESCRIPTION)
    players.default_member_permissions = permissions.manage_level

    @players.command(description='Link a player to a Discord user')
    @option(
        'player',
        input_type=PlayerConverter,
        description='The player to link',
        required=True,
        autocomplete=get_unlinked_players_for_channel)
    @option(
        'user',
        User,
        input_type=SlashCommandOptionType.user,
        description='The user to link to a Civilization 6 player',
        required=True)
    async def link(self, ctx: ApplicationContext, player: PlayerConverter, user: User):
        '''
        Links a player in the database to a Discord user by their ID.
        '''
        with get_session() as session:
            session.add(player)
            player.discordid = user.id
            session.commit()
            await ctx.respond(
                content=(f'{user.display_name} has been linked to player {player.name} and will be '
                'pinged on future turns.'),
                ephemeral=True)

    @players.command(description="Remove a player's link to a user")
    @option(
        'player',
        input_type=PlayerConverter,
        description='The player to unlink',
        required=True,
        autocomplete=get_linked_players_for_channel)
    async def unlink(self, ctx: ApplicationContext, player: PlayerConverter):
        '''
        Removes the link between a player in the database and its Discord ID.
        '''
        with get_session() as session:
            player = session.scalar(select(Player)
                .join(Player.webhookurl)
                .where(Player.name == player.name)
                .where(WebhookURL.channelid == ctx.channel_id))
            old_user = player.discordid
            player.discordid = None
            session.commit()
            if old_user:
                user = await ctx.bot.fetch_user(old_user)
                await ctx.respond(
                    content=(f'The link between {player.name} and {user.display_name} has been '
                        'removed'),
                    ephemeral=True)
                return
            await ctx.respond(
                content=(f"{player.name} doesn't seem to be linked to a user; the link was likely "
                    'already removed'),
                ephemeral=True)

    @players.command(description="Find which games associated with this channel a user is part of")
    @option(
        'user',
        User,
        input_type=SlashCommandOptionType.user,
        description="The user to find games for",
        required=True)
    async def games(self, ctx: ApplicationContext, user: User):
        '''
        Responds with a list of games the given user is a part of in the channel they interacted in.
        '''
        await ctx.respond(
            embed=player_messaging.get_player_games_embed(ctx.channel_id, user),
            ephemeral=True)

    @players.command(description="Find out which games a user is up in")
    @option(
        'user',
        User,
        input_type=SlashCommandOptionType.user,
        description="The user to find games for",
        required=True)
    async def upin(self, ctx: ApplicationContext, user: User):
        '''
        Responds with a list of games the given user is a part of, and currently up in, in the
        channel they interacted in.
        '''
        await ctx.respond(
            embed=player_messaging.get_player_upin_embed(ctx.channel_id, user),
            ephemeral=True)

def setup(bot: Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(PlayerCommands(bot))
