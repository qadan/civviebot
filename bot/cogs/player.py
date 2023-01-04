'''
CivvieBot cog to handle commands dealing with players.
'''

from discord import ApplicationContext, AutocompleteContext, Embed, SlashCommandOptionType, User
from discord.commands import SlashCommandGroup, option
from discord.ext.commands import Cog, Bot
from pony.orm import db_session
from bot.interactions import player as player_interactions
from bot.interactions.common import View
from bot.messaging import player as player_messaging
from utils import config, permissions
from utils.errors import NoGamesError, NoPlayersError
from utils.utils import get_discriminated_name, get_games_user_is_in

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

    @staticmethod
    def user_autocomplete(ctx: AutocompleteContext):
        '''
        Autocomplete for returning users in the channel.
        '''
        ctx.options = ctx.bot.fetch_user()

    @players.command(description='Link a player to a Discord user')
    @option(
        'user',
        User,
        input_type=SlashCommandOptionType.user,
        description='The user to link to a Civilization 6 player',
        required=True)
    async def link(self, ctx: ApplicationContext, user: User):
        '''
        Links a player in the database to a Discord user by their ID.
        '''
        try:
            await ctx.respond(
                content='Select a game containing the player you would like to link:',
                view=View(player_interactions.SelectGameForPlayers(
                    player_interactions.SelectPlayerForLink(
                        ctx.channel_id,
                        ctx.bot,
                        target_user=user),
                    ctx.channel_id,
                    ctx.bot,
                    target_user=user)),
                ephemeral=True)
        except NoGamesError:
            await ctx.respond(
                content=("I couldn't find any games in this channel with unlinked players that you "
                    'can link someone to'),
                ephemeral=True)
        except NoPlayersError:
            await ctx.respond(
                content=("I couldn't find any unlinked players in this channel that you can link "
                    'someone to.'),
                ephemeral=True)

    @players.command(description="Remove a player's link to a user")
    async def unlink(self, ctx: ApplicationContext):
        '''
        Removes the link between a player in the database and its Discord ID.
        '''
        try:
            await ctx.respond(
                content='Select a game containing the player to remove the link from:',
                view=player_messaging.get_player_unlink_view(ctx.channel_id, ctx.bot),
                ephemeral=True)
        except NoGamesError:
            await ctx.respond(
                content=("Sorry, I couldn't find any games in this server with players who could "
                    'be unlinked.'),
                ephemeral=True)
        except NoPlayersError:
            await ctx.respond(
                content="Sorry, I couldn't find any players in this server who could be unlinked.",
                ephemeral=True)

    @players.command(description="Remove a user's link to a player")
    @option(
        'user',
        User,
        input_type=SlashCommandOptionType.user,
        description='The user to unlink from a Civilization 6 player',
        required=True)
    async def unlinkuser(self, ctx: ApplicationContext, user: User):
        '''
        Removes the link from a user's Discord ID to whatever players it's connected to.
        '''
        try:
            await ctx.respond(
                content='Select a game the user is linked in:',
                view=View(player_interactions.SelectGameForPlayers(
                    player_interactions.UnlinkUserSelect(
                        ctx.channel_id,
                        ctx.bot,
                        target_user=user),
                    ctx.channel_id,
                    ctx.bot,
                    target_user=user)),
                ephemeral=True)
        except NoGamesError:
            await ctx.respond(
                content=("Sorry, I couldn't find any games with players "
                    f'{get_discriminated_name(user)} is linked to in this channel.'),
                ephemeral=True)
        except NoPlayersError:
            await ctx.respond(
                content=(f"Sorry, I couldn't find any players {get_discriminated_name(user)} is "
                    'linked to in this channel.'),
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
        with db_session():
            games = get_games_user_is_in(ctx.channel_id, user.id)
            if not games:
                await ctx.respond(
                    (f'{get_discriminated_name(user)} does not appear to be linked to any players '
                        'in any active games in this channel.'),
                    ephemeral=True)
                return

            game_list = Embed(
                title=f'Games {get_discriminated_name(user)} is part of:')
            game_list.description = '\n'.join([game.gamename for game in games])
        await ctx.respond(embed=game_list, ephemeral=True)

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
