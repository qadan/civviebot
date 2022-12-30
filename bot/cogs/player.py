'''
CivvieBot cog to handle commands dealing with players.
'''

from time import time
from discord import ApplicationContext, Embed, SlashCommandOptionType
from discord.commands import SlashCommandGroup, option
from discord.ext.commands import Cog, Bot, UserConverter
from pony.orm import db_session, left_join
from bot.cogs.base import NAME as base_name
from bot.interactions import player as player_interactions
from bot.interactions.common import View
from database.models import Game
from utils import config, permissions
from utils.errors import NoGamesError, NoPlayersError
from utils.utils import expand_seconds_to_string, get_discriminated_name


NAME = config.get('command_prefix') + 'player'
DESCRIPTION = 'Manage known players and user links in this channel.'
NO_PLAYERS = ("I couldn't find any players being tracked in this channel that fit the conditions "
    f'you gave. You may need to start a game first; use `/{base_name} quickstart` for a how-to.')
NO_GAMES = ("I couldn't find any games being tracked in this channel that fit the conditions you "
    f'gave. You may need to start a game first; use `/{base_name} quickstart` for a how-to.')


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
        'user',
        UserConverter,
        input_type=SlashCommandOptionType.user,
        description='The user to link to a Civilization 6 player',
        required=True)
    async def link(self, ctx: ApplicationContext, user: UserConverter):
        '''
        Links a player in the database to a Discord user by their ID.
        '''
        try:
            await ctx.respond(
                content='Select the player you would like to link:',
                view=View(player_interactions.SelectGameForPlayers(
                    player_interactions.UnlinkedPlayerSelect(
                        ctx.channel_id,
                        ctx.bot,
                        initiating_user=user),
                    ctx.channel_id,
                    ctx.bot,
                    initiating_user=user)),
                ephemeral=True)
        except NoGamesError:
            await ctx.respond(NO_GAMES, ephemeral=True)
        except NoPlayersError:
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
                view=View(player_interactions.SelectGameForPlayers(
                    player_interactions.UnlinkPlayerSelect(
                        ctx.channel_id,
                        ctx.bot),
                    ctx.channel_id,
                    ctx.bot)),
                ephemeral=True)
        except NoGamesError:
            await ctx.respond(NO_GAMES, ephemeral=True)
        except NoPlayersError:
            await ctx.respond(NO_PLAYERS, ephemeral=True)


    @players.command(description="Remove a user's link to a player")
    @option(
        'user',
        UserConverter,
        input_type=SlashCommandOptionType.user,
        description='The user to unlink from a Civilization 6 player',
        required=True)
    async def unlinkuser(self, ctx: ApplicationContext, user: UserConverter):
        '''
        Removes the link from a user's Discord ID to whatever players it's connected to.
        '''
        try:
            await ctx.respond(
                view=View(player_interactions.SelectGameForPlayers(
                    player_interactions.UnlinkUserSelect(
                        ctx.channel_id,
                        ctx.bot,
                        initiating_user=user),
                    ctx.bot,
                    ctx.channel_id,
                    initiating_user=user)),
                ephemeral=True)
        except NoGamesError:
            await ctx.respond(NO_GAMES, ephemeral=True)
        except NoPlayersError:
            await ctx.respond(NO_PLAYERS, ephemeral=True)


    @players.command(description="Find which games associated with this channel a user is part of")
    @option(
        'user',
        UserConverter,
        input_type=SlashCommandOptionType.user,
        description="The user to find games for. Leave empty to get games you're a part of",
        required=True)
    async def games(self, ctx: ApplicationContext, user: UserConverter):
        '''
        Responds with a list of games the given user is a part of in the channel they interacted in.
        '''
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
        input_type=SlashCommandOptionType.user,
        description="The user to find games for.",
        required=True)
    async def upin(self, ctx: ApplicationContext, user: UserConverter):
        '''
        Responds with a list of games the given user is a part of, and currently up in, in the
        channel they interacted in.
        '''
        with db_session():
            games = left_join(g for g in Game for p in g.players if
                g.webhookurl.channelid == ctx.interaction.channel_id and
                g.lastup == p and
                p.discordid == user.id)
            if not games:
                username = f'{get_discriminated_name(user)} does' if user else 'You do'
                return await ctx.respond(
                    (f'{username} does not appear to be linked to any players whose turn is up in '
                    'any active games in this channel'),
                    ephemeral=True)

            game_list = Embed(
                title=(f'Games tracked in this channel {get_discriminated_name(user)} is currently '
                    'up in:'))
            games = [(f'{game.gamename} (turn {game.turn} - '
                f'{expand_seconds_to_string(time() - game.lastturn)} ago)') for game in games]
            game_list.description = '\n'.join(games)
        await ctx.respond(embed=game_list, ephemeral=True)


def setup(bot: Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(PlayerCommands(bot))
