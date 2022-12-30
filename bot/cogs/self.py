'''
CivvieBot cog to handle commands dealing with one's own players.

Identical in functionality to the 'player' cog, but all of the commands only deal with the invoking
user.
'''

from time import time
from discord import ApplicationContext, Embed
from discord.commands import SlashCommandGroup
from discord.ext.commands import Bot, Cog
from pony.orm import db_session, left_join
from bot.interactions import player as player_interactions
from bot.interactions.common import View
from database.models import Game
from utils.errors import NoPlayersError, NoGamesError
from utils.utils import expand_seconds_to_string, get_discriminated_name
from bot.cogs.base import NAME as base_name
from bot.cogs.player import NO_PLAYERS
from utils import config, permissions

NAME = config.get('command_prefix') + 'self'
DESCRIPTION = 'Manage your own user links and players in this channel.'
NO_GAMES = ("I couldn't find any games being tracked in this channel. You may need to start "
    f'a game first; use `/{base_name} quickstart` for a how-to.')

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
    async def link(self, ctx: ApplicationContext):
        '''
        Links a player in the database to the initiating user.
        '''
        try:
            await ctx.respond(
                content='Select the game containing the player you would like to link yourself to:',
                view=View(player_interactions.SelectGameForUnlinkedPlayers(
                    player_interactions.UnlinkedPlayerSelect(
                        ctx.channel_id,
                        ctx.bot,
                        initiating_user=ctx.user),
                    ctx.channel_id,
                    ctx.bot,
                    initiating_user=ctx.user)),
                ephemeral=True)
        except NoGamesError:
            await ctx.respond(NO_GAMES, ephemeral=True)
        except NoPlayersError:
            await ctx.respond(NO_PLAYERS, ephemeral=True)


    @selfcommands.command(description="Remove a player's link to you")
    async def unlink(self, ctx: ApplicationContext):
        '''
        Removes the link between a player in the database and its Discord ID.

        In practice, this is just setting the ID to an empty string.
        '''
        try:
            await ctx.respond(
                content="Select the game that the player you wish to unlink is in:",
                view=View(player_interactions.SelectGameForLinkedPlayers(
                    player_interactions.UnlinkPlayerSelect(
                        ctx.channel_id,
                        ctx.bot,
                        initiating_user=ctx.user),
                    ctx.channel_id,
                    ctx.bot,
                    initiating_user=ctx.user)),
                ephemeral=True)
        except NoGamesError:
            await ctx.respond(NO_GAMES, ephemeral=True)
        except NoPlayersError:
            await ctx.respond(NO_PLAYERS, ephemeral=True)


    @selfcommands.command(description="Find which games associated with this channel you're part of")
    async def games(self, ctx: ApplicationContext):
        '''
        Responds with a list of games the given user is a part of in the channel they interacted in.
        '''
        disc_name = get_discriminated_name(ctx.user)
        with db_session():
            games = left_join(g for g in Game for p in g.players if
                g.webhookurl.channelid == ctx.interaction.channel_id and
                p in g.players and
                p.discordid == ctx.user.id)
            if not games:
                await ctx.respond(
                    (f'{disc_name} does not appear to be linked to any players in any active games '
                        'in this channel.'),
                    ephemeral=True)
                return

            game_list = Embed(title=f'Games {disc_name} is part of in this channel:')
            game_list.add_field(name='Games', value='\n'.join([game.gamename for game in games]))
        await ctx.respond(embed=game_list, ephemeral=True)


    @selfcommands.command(description="Find out which games you're up in")
    async def upin(self, ctx: ApplicationContext):
        '''
        Responds with a list of games the given user is a part of, and currently up in, in the
        channel they interacted in.
        '''
        with db_session():
            games = left_join(g for g in Game for p in g.players if
                g.webhookurl.channelid == ctx.interaction.channel_id and
                g.lastup == p and
                p.discordid == ctx.user.id)
            if not games:
                await ctx.respond(
                    ('You do not appear to be linked to any players whose turn is up in any active '
                    'games in this channel'),
                    ephemeral=True)
                return

            game_list = Embed(
                title=(f"Games tracked in this channel you're currently up in:"))
            games = [(f'{game.gamename} (turn {game.turn} - '
                f'{expand_seconds_to_string(time() - game.lastturn)} ago)') for game in games]
            game_list.add_field(name='Games:', value='\n'.join(games))
        await ctx.respond(embed=game_list, ephemeral=True)


def setup(bot: Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(SelfCommands(bot))