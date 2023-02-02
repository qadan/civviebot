'''
CivvieBot cog to handle commands dealing with Webhook URLs.
'''

from discord import ApplicationContext, Embed
from discord.commands import SlashCommandGroup, option
from discord.ext.commands import Cog, Bot
from bot import permissions
from database.connect import get_session
from database.utils import get_url_for_channel
from utils import config


NAME = config.COMMAND_PREFIX + 'url'
DESCRIPTION = 'Manage webhook URLs in this channel.'


class WebhookURLCommands(Cog, name=NAME, description=DESCRIPTION):
    '''
    Command group for creating, modifying, removing, and getting information
    about Webhook URLs.
    '''

    def __init__(self, bot):
        '''
        Initialization; sets the bot.
        '''
        self.bot: Bot = bot

    urls = SlashCommandGroup(
        NAME,
        'Get information the URL that tracks games in this channel.'
    )
    urls.default_member_permissions = permissions.base_level

    @urls.command(
        description="Responds with this channel's Civilization 6 webhook URL"
    )
    @option(
        'private',
        type=bool,
        description='Make the response visible only to you',
        default=False
    )
    async def get(self, ctx: ApplicationContext, private: bool):
        '''
        Responds with an embed containing webhook URL information.
        '''
        with get_session() as session:
            url = get_url_for_channel(ctx.channel_id)
            session.add(url)
            content = ''
            embed = Embed(title=f'Webhook URL for {ctx.channel.name}')
            embed.add_field(name='URL', value=url.full_url)
            if url.games:
                embed.add_field(name='Games tracked', value=len(url.games))
                embed.set_footer(
                    text=(
                        'For usage instructions, use "/'
                        f'{config.COMMAND_PREFIX} quickstart". To get the '
                        'list of games tracked in this channel, use "/'
                        f'{config.COMMAND_PREFIX}game list".'
                    )
                )
            else:
                content = (
                    "There aren't any games being tracked in this channel; "
                    f"you'll have to use `/{config.COMMAND_PREFIX}tracking "
                    "add` to start using this URL.\n\nFor more info, use `/"
                    f"{config.COMMAND_PREFIX} quickstart`."
                )
            await ctx.respond(content=content, embed=embed, ephemeral=private)


def setup(bot: Bot):
    '''
    Adds this cog to the bot.
    '''
    bot.add_cog(WebhookURLCommands(bot))
