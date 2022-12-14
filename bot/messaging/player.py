'''
Builders for different parts of messages sent about players.
'''

from typing import Set, Tuple
from discord import Embed

def get_user_unlink_embed(results: Set[Tuple[str, str]]) -> Embed:
    '''
    Gets the embed for the results of user to player unlinking.

    The results passed in should be a set of tuples, each with the form ('name', 'result').
    '''
    embed = Embed(
        title='Unlinked players',
        description='Links removed from the following players:')
    for playername, result in results:
        embed.add_field(
            name=playername,
            value=result)
    return embed
