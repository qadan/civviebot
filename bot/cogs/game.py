'''
CivvieBot cog to handle commands dealing with games.
'''

from discord import ApplicationContext
from discord.commands import SlashCommandGroup, option
from discord.ext.commands import Cog, Bot
from bot.interactions.common import View
import bot.interactions.game as game_interactions
import bot.messaging.game as game_messaging
from utils import config, permissions
from utils.errors import NoGamesError

NAME = config.get('command_prefix') + 'game'
DESCRIPTION = 'Manage games in this channel that are being tracked by CivvieBot.'

class GameCommands(Cog, name=NAME, description=DESCRIPTION):
    '''
    Command group for working with Game objects in the database.
    '''

    def __init__(self, bot):
        '''
        Initialization; sets the bot.
        '''
        self.bot: Bot = bot

    games = SlashCommandGroup(
        NAME,
        'Get information about games in this channel that are being tracked by CivvieBot.')
    games.default_member_permissions = permissions.base_level
    manage_games = SlashCommandGroup(NAME + '_manage', DESCRIPTION)
    manage_games.default_member_permissions = permissions.manage_level

    @games.command(description='Get information about an active game in this channel')
    @option(
        'private',
        type=bool,
        description='Make the response visible only to you',
        default=True)
    async def info(self, ctx: ApplicationContext, private: bool):
        '''
        Prints out information about one game.
        '''
        try:
            await ctx.respond(
                content='Select an active game to get information about:',
                view=View(game_interactions.SelectGameForInfo(ctx.channel_id, ctx.bot)),
                ephemeral=private)
        except NoGamesError:
            await ctx.respond(
                content="Sorry, I couldn't find any games in this channel to get info about.",
                ephemeral=True)

    @manage_games.command(description='Edit the configuration for an active game in this channel')
    async def edit(self, ctx: ApplicationContext):
        '''
        Modifies the configuration for a game given the passed-in options.
        '''
        await ctx.respond(
            content='Select an active game to edit:',
            view=View(game_interactions.SelectGameForEdit(ctx.channel_id, ctx.bot)),
            ephemeral=True)

    @manage_games.command(
        description='Toggle notification muting for an active game in this channel')
    async def toggle_mute(self, ctx: ApplicationContext):
        '''
        Toggles notification muting for a game on or off.
        '''
        await ctx.respond(
            content=('Select a game to toggle notifications for:\n🔊: currently unmuted\n🔇: '
                'currently muted'),
            view=View(game_interactions.SelectGameForMute(ctx.channel_id, ctx.bot)),
            ephemeral=True)

    @manage_games.command(
        description='Deletes information about an active game and its players in this channel.')
    async def delete(self, ctx: ApplicationContext):
        '''
        Deletes a game and its associated players from the database.
        '''
        await ctx.respond(
            content='Select a game to delete:',
            view=View(game_interactions.SelectGameForDelete(ctx.channel_id, ctx.bot)),
            ephemeral=True)

    @manage_games.command(
        description='Sends a fresh turn notification for an active game in this channel')
    async def ping(self, ctx: ApplicationContext):
        '''
        Re-sends a turn notification for the most recent turn in a game.
        '''
        await ctx.respond(
            content='Select a game to ping:',
            view=View(game_interactions.SelectGameForPing(ctx.channel_id, ctx.bot)),
            ephemeral=True)

    @manage_games.command(
        description='Get info about the game cleanup schedule, or manually trigger cleanup')
    async def cleanup(self, ctx: ApplicationContext):
        '''
        Sends info about the game cleanup schedule, and allows cleanup to be triggered.
        '''
        await ctx.respond(
            content=game_messaging.CONTENT,
            embed=game_messaging.get_cleanup_embed(channel=ctx.channel_id),
            view=View(game_interactions.TriggerCleanupButton(self.bot)),
            ephemeral=True)

def setup(bot: Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(GameCommands(bot))
