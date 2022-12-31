'''
CivvieBot cog to handle commands dealing with one's own players.

Identical in functionality to the 'player' cog, but all of the commands only deal with the invoking
user.
'''

from discord import ApplicationContext, Embed
from discord.commands import SlashCommandGroup
from discord.ext.commands import Bot, Cog
from pony.orm import db_session
from bot.cogs.base import NAME as base_name
from bot.interactions import player as player_interactions
from bot.interactions.common import View
from bot.messaging import player as player_messaging
from utils.errors import NoPlayersError, NoGamesError
from utils.utils import get_games_user_is_in
from utils import config, permissions

NAME = config.get('command_prefix') + 'self'
DESCRIPTION = 'Manage your own user links and players in this channel.'
NO_GAMES = ("I couldn't find any games being tracked in this channel. You may need to start "
    f'a game first; use `/{base_name} quickstart` for a how-to.')
NO_PLAYERS = ("Sorry, I couldn't find any players being tracked in this channel linked to that "
    'user that fit those conditions.')

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
                        target_user=ctx.user),
                    ctx.channel_id,
                    ctx.bot,
                    target_user=ctx.user)),
                ephemeral=True)
        except NoGamesError:
            await ctx.respond(NO_GAMES, ephemeral=True)
        except NoPlayersError:
            await ctx.respond(
                content=("Sorry, I couldn't find any players in this channel you can link yourself "
                    'to.'),
                ephemeral=True)

    @selfcommands.command(description="Remove a player's link to you")
    async def unlink(self, ctx: ApplicationContext):
        '''
        Removes the link between a player in the database and its Discord ID.

        In practice, this is just setting the ID to an empty string.
        '''
        try:
            await ctx.respond(
                content="Select the game that the player you wish to unlink is in:",
                view=player_messaging.get_player_unlink_view(
                    ctx.channel_id,
                    ctx.bot,
                    target_user=ctx.user),
                ephemeral=True)
        except NoGamesError:
            await ctx.respond(
                content=("Sorry, I couldn't find any games with players that you're linked to "
                    'in this channel.'),
                ephemeral=True)
        except NoPlayersError:
            await ctx.respond(
                content="Sorry, I couldn't find any players you're linked to in this channel.",
                ephemeral=True)

    @selfcommands.command(
        description="Find which games associated with this channel you're part of")
    async def games(self, ctx: ApplicationContext):
        '''
        Responds with a list of games the given user is a part of in the channel they interacted in.
        '''
        with db_session():
            games = get_games_user_is_in(ctx.user, ctx.channel_id)
            if not games:
                await ctx.respond(
                    ('You do not appear to be linked to any players in any active games '
                        'in this channel.'),
                    ephemeral=True)
                return

            game_list = Embed(title='Games you are part of in this channel:')
            game_list.description = '\n'.join([game.gamename for game in games])
        await ctx.respond(embed=game_list, ephemeral=True)

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
