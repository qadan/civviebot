'''
CivvieBot cog to handle commands dealing with players.
'''

from discord import ApplicationContext, User, Embed
from discord.commands import SlashCommandGroup, option
from discord.ui import View
from discord.ext.commands import Cog, Bot, UserConverter
from pony.orm import db_session, left_join
from bot.cogs.base import NAME as base_name
from bot.interactions import player as player_interactions
from database.models import Game
from utils import config
from utils.utils import get_discriminated_name


NAME = config.get('command_prefix') + 'player'
DESCRIPTION = 'Manage known players and user links in this channel.'
NO_PLAYERS = ("I couldn't find any players being tracked in this channel. You may need to start "
    f'a game first; use `/{base_name} quickstart` for a how-to.')


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


    @players.command(description='Link a player to a Discord user')
    async def link(self, ctx: ApplicationContext):
        '''
        Links a player in the database to a Discord user by their ID.
        '''
        try:
            await ctx.respond(
                content='Select the player you would like to link:',
                view=View(player_interactions.UnlinkedPlayerSelect(ctx.channel_id, ctx.bot)),
                ephemeral=True)
        except player_interactions.NoPlayersError:
            await ctx.respond(NO_PLAYERS, ephemeral=True)


    @players.command(description="Remove a player's link to a user")
    async def unlinkplayer(self, ctx: ApplicationContext):
        '''
        Removes the link between a player in the database and its Discord ID.

        In practice, this is just setting the ID to an empty string.
        '''
        try:
            await ctx.respond(
                content='Select a player to remove the link from:',
                view=View(player_interactions.UnlinkPlayerSelect(ctx.channel_id, ctx.bot)),
                ephemeral=True)
        except player_interactions.NoPlayersError:
            await ctx.respond(NO_PLAYERS, ephemeral=True)


    @players.command(description="Remove a user's link to a player")
    @option(
        'user',
        UserConverter,
        input_type=User,
        description='The user to unlink from a Civilization 6 player',
        required=False)
    async def unlinkuser(self, ctx: ApplicationContext, user: UserConverter = None):
        '''
        Removes the link from a user's Discord ID to whatever players it's connected to.
        '''
        if user is None:
            user = ctx.user
        await ctx.send_modal(player_interactions.UnlinkUserModal(
            ctx.channel_id,
            ctx.bot,
            user))


    @players.command(description="Find which games associated with this channel a user is part of")
    @option(
        'user',
        UserConverter,
        input_type=User,
        description="The user to find games for. Leave empty to get games you're a part of",
        required=False)
    async def games(self, ctx: ApplicationContext, user: UserConverter = None):
        '''
        Responds with a list of games the given user is a part of in the channel they interacted in.
        '''
        if user is None:
            user = ctx.user
        with db_session():
            games = left_join(g for g in Game for p in g.players if
                g.webhookurl.channelid == ctx.interaction.channel_id and
                p in g.players and
                p.discordid == user.id)
            if not games:
                await ctx.respond(
                    (f'{get_discriminated_name(user)} does not appear to be linked to any players '
                        'in any active games in this channel.'),
                    ephemeral=True)
                return

            game_list = Embed(title=f'Games {user.display_name} is part of in this channel:')
            game_list.add_field(name='Games', value='\n'.join([game.gamename for game in games]))
        await ctx.respond(embed=game_list, ephemeral=True)


    @players.command(description="Find out which games a user is up in")
    @option(
        'user',
        UserConverter,
        input_type=User,
        description="The user to find games for. Leave empty to get games you're up in",
        required=False)
    async def upin(self, ctx: ApplicationContext, user: UserConverter = None):
        '''
        Responds with a list of games the given user is a part of, and currently up in, in the
        channel they interacted in.
        '''
        if user is None:
            user = ctx.user
        with db_session():
            games = left_join(g for g in Game for p in g.players if
                g.webhookurl.channelid == ctx.interaction.channel_id and
                g.lastup == p and
                p.discordid == user.id)
            if not games:
                username = f'{get_discriminated_name(user)} does' if user else 'You do'
                return await ctx.respond(
                    (f'{username} not appear to be linked to any players whose turn is up in any '
                    'active games in this channel'),
                    ephemeral=True)

            game_list = Embed(
                title=(f'Games {user.display_name} is part of in this channel and is currently up '
                    'in:'))
            game_list.add_field(name='Games', value='\n'.join([game.gamename for game in games]))
        await ctx.respond(game_list, ephemeral=True)


def setup(bot: Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(PlayerCommands(bot))
