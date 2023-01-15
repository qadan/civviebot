'''
CivvieBot cog to handle commands dealing with games.
'''

import logging
from discord import ApplicationContext, Embed, EmbedField
from discord.commands import SlashCommandGroup, option
from discord.ext.commands import Cog, Bot
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from bot.interactions.common import View
import bot.interactions.common as common_interactions
import bot.interactions.game as game_interactions
import bot.messaging.game as game_messaging
import bot.messaging.notify as notify_messaging
from database.autocomplete import get_games_for_channel
from database.converters import GameConverter
from database.models import Game, Player, PlayerGames
from database.utils import get_session, get_url_for_channel
from utils import config, permissions
from utils.string import get_display_name

logger = logging.getLogger(f'civviebot.{__name__}')
NAME = config.COMMAND_PREFIX + 'game'
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
    manage_games = SlashCommandGroup(NAME + 'manage', DESCRIPTION)
    manage_games.default_member_permissions = permissions.manage_level

    @manage_games.command(description='Add a game name to track in this channel')
    @option(
        'game_name',
        input_type=str,
        description='The (case, space and punctuation-sensitive) name of the game to add',
        required=True)
    async def add(self, ctx: ApplicationContext, game_name: str):
        '''
        Adds a new game to track in this channel.
        '''
        url = get_url_for_channel(ctx.channel_id)
        with get_session() as session:
            session.add(url)
            try:
                session.add(Game(name=game_name, slug=url.slug))
                session.commit()
                embed = Embed()
                embed.add_field(name='Channel URL', value=url.full_url)
                embed.set_footer(text=(f'Use "/{config.COMMAND_PREFIX} quickstart" if you need '
                    'setup instructions. To change how notifications work for this game, use "'
                    f'{config.COMMAND_PREFIX}gamemanage edit"'))
                await ctx.respond(
                    content=f"Tracking a new game in this channel: **{game_name}**",
                    embed=embed)
                return
            except IntegrityError:
                await ctx.respond(
                    content=("I'm already tracking a game in this channel by that name; you can "
                        "just set the **Play By Cloud Webhook URL** in Civilization 6 to "
                        f"{url.full_url} if you'd like to pop notifications for it in here. For "
                        f"more details, use `/{config.COMMAND_PREFIX} quickstart`, or if you'd "
                        "like to know what I've tracked for this game so far (if anything), use "
                        f"`/{config.COMMAND_PREFIX}game info`."),
                    ephemeral=True)
                return

    @games.command(description='Get information about an active game in this channel')
    @option(
        'game',
        input_type=GameConverter,
        description='The game to get info about',
        required=True,
        autocomplete=get_games_for_channel)
    @option(
        'private',
        type=bool,
        description='Make the response visible only to you',
        default=True)
    async def info(self, ctx: ApplicationContext, game: GameConverter, private: bool):
        '''
        Prints out information about one game.
        '''
        embed = await game_messaging.get_info_embed(game, ctx.bot)
        await ctx.respond(
            content=None,
            embed=embed,
            ephemeral=private)

    @games.command(description='Get a list of known players for a game in this channel')
    @option(
        'game',
        input_type=GameConverter,
        description='The game to get players for',
        required=True,
        autocomplete=get_games_for_channel)
    @option(
        'private',
        type=bool,
        description='Make the response visible only to you',
        default=True)
    async def players(
        self,
        ctx: ApplicationContext,
        game: GameConverter,
        private: bool):
        '''
        Prints out a list of known players in this game.
        '''
        content = None
        embed = None
        def player_to_field(player: Player, bot: Bot) -> EmbedField:
            if player.discordid:
                user = bot.get_user(int(player.discordid))
                link = get_display_name(user) if user else (f'MISSING '
                    f'(`/{config.COMMAND_PREFIX}playermanage unlink` to remove)')
            else:
                link = 'No linked user'
            return EmbedField(name=player.name, value=link, inline=True)
        with get_session() as session:
            session.add(game)
            players = session.scalars(select(Player)
                .join(PlayerGames, PlayerGames.playername == Player.name)
                .where(PlayerGames.gamename == game.name)).all()
            if players:
                embed = Embed(title='Players')
                embed.fields = [player_to_field(player, self.bot) for player in players]
            else:
                content = ("There aren't any players being tracked for this game; likely I "
                    "haven't gotten any notifications from Civilization 6 yet.")
        await ctx.respond(content=content, embed=embed, ephemeral=private)

    @manage_games.command(description='Edit the configuration for an active game in this channel')
    @option(
        'game',
        input_type=GameConverter,
        description='The game to edit',
        required=True,
        autocomplete=get_games_for_channel)
    async def edit(self, ctx: ApplicationContext, game: GameConverter):
        '''
        Modifies the configuration for a game given the passed-in options.
        '''
        await ctx.send_modal(game_interactions.GameEditModal(
            game.name,
            ctx.channel_id,
            self.bot,
            common_interactions.NotifyIntervalInput(remind_interval=game.remindinterval),
            common_interactions.MinTurnsInput(min_turns=game.minturns),
            title=f'Editing information about {game.name}'))

    @manage_games.command(
        description='Toggle notification muting for an active game in this channel')
    @option(
        'game',
        input_type=GameConverter,
        description='The game to toggle muting for',
        required=True,
        autocomplete=get_games_for_channel)
    async def toggle_mute(self, ctx: ApplicationContext, game: GameConverter):
        '''
        Toggles notification muting for a game on or off.
        '''
        with get_session() as session:
            session.add(game)
            game.muted = not game.muted
            session.commit()
            await ctx.respond(
                content=(f'Notifications for the game **{game.name}** are now muted.'
                    if game.muted
                    else f'Notifications for the game **{game.name}** are now unmuted.'),
                ephemeral=True)

    @manage_games.command(
        description="Removes a tracked game from this channel and cleans up info about it.")
    @option(
        'game',
        input_type=GameConverter,
        description='The game to delete',
        required=True,
        autocomplete=get_games_for_channel)
    async def delete(self, ctx: ApplicationContext, game: GameConverter):
        '''
        Deletes a game and its associated data from the database.
        '''
        embed = await game_messaging.get_info_embed(game, ctx.bot)
        await ctx.respond(
            content=(f'Are you sure you want to delete **{game.name}**? This will remove any '
                'attached players that are not currently part of any other game.'),
            embed=embed,
            view=View(game_interactions.ConfirmDeleteButton(game)))

    @manage_games.command(
        description='Sends a fresh turn notification for an active game in this channel')
    @option(
        'game',
        input_type=GameConverter,
        description='The game to ping',
        required=True,
        autocomplete=get_games_for_channel)
    async def ping(self, ctx: ApplicationContext, game: GameConverter):
        '''
        Re-sends a turn notification for the most recent turn in a game.
        '''
        with get_session() as session:
            session.add(game)
            logger.info(
                'User %s requested re-pinging for game %s (channel ID: %d)',
                get_display_name(ctx.user),
                game.name,
                ctx.channel_id)
            if not game.turns:
                await ctx.respond(
                    content=("Sorry; I haven't gotten a turn notification for this game yet, so I "
                        "can't tell who's up."),
                    ephemeral=True)
                return
            await ctx.respond(
                content=notify_messaging.get_content(game.turns[0]),
                embed=notify_messaging.get_embed(game.turns[0]),
                view=notify_messaging.get_view(game.turns[0]))

    @manage_games.command(
        description='Get info about the game cleanup schedule, or manually trigger cleanup')
    async def cleanup(self, ctx: ApplicationContext):
        '''
        Sends info about the game cleanup schedule, and allows cleanup to be triggered.
        '''
        await ctx.respond(
            content=game_messaging.CLEANUP_CONTENT,
            embed=game_messaging.get_cleanup_embed(channel=ctx.channel_id),
            view=View(game_interactions.TriggerCleanupButton(self.bot)),
            ephemeral=True)

def setup(bot: Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(GameCommands(bot))
