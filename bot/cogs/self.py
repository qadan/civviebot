'''
CivvieBot cog to handle commands dealing with one's own players.

Identical in functionality to the 'player' cog, but all of the commands only deal with the invoking
user.
'''

from discord import ApplicationContext, Embed
from discord.commands import SlashCommandGroup
from discord.ui import View
from discord.ext.commands import Bot, Cog
from pony.orm import db_session, left_join
from bot.interactions import player as player_interactions
from database.models import Game
from utils.utils import get_discriminated_name
from bot.cogs.player import NO_PLAYERS
from utils import config

NAME = config.get('command_prefix') + 'self'
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


    @selfcommands.command(description='Link yourself to a player')
    async def link(self, ctx: ApplicationContext):
        '''
        Links a player in the database to the .
        '''
        try:
            await ctx.respond(
                content='Select the player you would like to link:',
                view=View(player_interactions.UnlinkedPlayerSelect(
                    ctx.channel_id,
                    ctx.bot,
                    initiating_user=ctx.user)),
                ephemeral=True)
        except player_interactions.NoPlayersError:
            await ctx.respond(NO_PLAYERS, ephemeral=True)


    @selfcommands.command(description="Remove a player's link to you")
    async def unlinkplayer(self, ctx: ApplicationContext):
        '''
        Removes the link between a player in the database and its Discord ID.

        In practice, this is just setting the ID to an empty string.
        '''
        try:
            await ctx.respond(
                content='Select a player to remove the link from:',
                view=View(player_interactions.UnlinkPlayerSelect(
                    ctx.channel_id,
                    ctx.bot,
                    initiating_user=ctx.user)),
                ephemeral=True)
        except player_interactions.NoPlayersError:
            await ctx.respond(NO_PLAYERS, ephemeral=True)


    @selfcommands.command(description="Removes your link to a player")
    async def unlinkuser(self, ctx: ApplicationContext):
        '''
        Removes the link from a user's Discord ID to whatever players it's connected to.
        '''
        await ctx.send_modal(player_interactions.UserLinkedPlayerSelect(
            ctx.channel_id,
            ctx.bot,
            initiating_user=ctx.user))


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
                return await ctx.respond(
                    ('You do not appear to be linked to any players whose turn is up in any active '
                    'games in this channel'),
                    ephemeral=True)

            game_list = Embed(
                title=(f'Games {get_discriminated_name(ctx.user)} is part of in this channel and '
                    'is currently up in:'))
            game_list.add_field(name='Games', value='\n'.join([game.gamename for game in games]))
        await ctx.respond(game_list, ephemeral=True)


def setup(bot: Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(SelfCommands(bot))