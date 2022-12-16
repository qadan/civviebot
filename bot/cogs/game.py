'''
CivvieBot cog to handle commands dealing with games.
'''

from discord import ApplicationContext
from discord.commands import SlashCommandGroup, option
from discord.ui import View
from discord.ext.commands import Cog, Bot
import bot.interactions.game as game_interactions
import bot.messaging.game as game_messaging
from utils import config


NAME = config.get('command_prefix') + 'game'
DESCRIPTION = 'Manage active games in this channel that are being tracked by CivvieBot.'


class GameCommands(Cog, name=NAME, description=DESCRIPTION):
    '''
    Command group for working with Game objects in the database.
    '''

    def __init__(self, bot):
        '''
        Initialization; sets the bot.
        '''
        self.bot: Bot = bot


    games = SlashCommandGroup(NAME, DESCRIPTION)


    @games.command(description='Get information about an active game in this channel')
    async def info(self, ctx: ApplicationContext):
        '''
        Prints out information about one game.
        '''
        await ctx.respond(
            content='Select an active game to get information about:',
            view=View(game_interactions.SelectGameForInfo(ctx.channel_id, ctx.bot)),
            ephemeral=True)


    @games.command(description='Edit the configuration for an active game in this channel')
    async def edit(self, ctx: ApplicationContext):
        '''
        Modifies the configuration for a game given the passed-in options.
        '''
        await ctx.respond(
            content='Select an active game to edit:',
            view=View(game_interactions.SelectGameForEdit(ctx.channel_id, ctx.bot)),
            ephemeral=True)


    @games.command(description='Toggle notification muting for an active game in this channel')
    async def toggle_mute(self, ctx: ApplicationContext):
        '''
        Toggles notification muting for a game on or off.
        '''
        await ctx.respond(
            content=('Select a game to toggle notifications for (games with a 🔇 are currently '
                'muted, and games with a 🔊 are not):'),
            view=View(game_interactions.SelectGameForMute(ctx.channel_id, ctx.bot)),
            ephemeral=True)


    @games.command(
        description='Deletes information about an active game and its players in this channel.')
    async def delete(self, ctx: ApplicationContext):
        '''
        Deletes a game and its associated players from the database.
        '''
        await ctx.respond(
            content='Select a game to delete:',
            view=View(game_interactions.SelectGameForDelete(ctx.channel_id, ctx.bot)),
            ephemeral=True)


    @games.command(description='Sends a fresh turn notification for an active game in this channel')
    async def ping(self, ctx: ApplicationContext):
        '''
        Re-sends a turn notification for the most recent turn in a game.
        '''
        await ctx.respond(
            content='Select a game to ping:',
            view=View(game_interactions.SelectGameForPing(ctx.channel_id, ctx.bot)),
            ephemeral=True)


    @games.command(description='Lists all active games in this channel')
    @option(
        'private',
        type=bool,
        description='Make the response visible only to you',
        default=True)
    async def list(self, ctx: ApplicationContext, private: bool):
        '''
        Sends a list of all active games in the context's channel.
        '''
        await ctx.respond(embed=game_messaging.get_game_list_embed(ctx), ephemeral=private)


def setup(bot: Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(GameCommands(bot))
