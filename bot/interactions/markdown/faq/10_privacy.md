What exactly do you track about me/my server?
These are the most important things I track with reference to your privacy:

* When someone asks for a channel's webhook URL for the first time using using `%COMMAND_PREFIX%url get` or `%COMMAND_PREFIXgamemanage add`, I generate one and tie it to that channel's snowflake. I don't store any information about a server other than these snowflakes.
* I keep a record of each player by the reported name that I get from Civilization 6; these are tied to the channel's snowflake.
* When someone links a player to a Discord user, I add the Discord user's snowflake to the player record.

**What do you mean by "snowflake"?**

Discord uses Twitter-style snowflakes - numbers that uniquely identify something in the app like a user or a channel. They're not called IDs because they're more than just a uniquely identifying number - they also contain another couple of pieces of information, like the exact time that user or channel or whatever was created.

That being said, Discord snowflakes _are_ public information (to an extent); if you can see something on Discord, you can see its snowflake, so I'm not ever hanging onto anything anyone in a channel isn't already privy to.

Discord has a little more information about snowflakes if you'd like to peruse a rather dry reference manual: https://discord.com/developers/docs/reference#snowflakes

Everything I do, from notifications to autocompletes, is directly tied to the snowflake of the channel it came from.

**How long do you hang onto information, and how do I get rid of it?**

* I hang onto webhook URLs as long as I'm in the channel they're attached to. If I'm removed from a channel, the URL and all associated data is removed.
* I hang onto games as long as they're active - meaning as long as they haven't been automatically cleaned up or I'm removed from the game's channel. Individual games can be manually removed using `/%COMMAND_PREFIX%gamemanage delete`.
* I hang onto a player's linked Discord snowflake for as long as I hang onto the player - but that can be removed at any time using `/%COMMAND_PREFIX%self unlink` or `/%COMMAND_PREFIX%playermanage unlink`, or using the unlink button on that player's turn.

Use `/%COMMAND_PREFIX%gamemanage cleanup` to get information about the cleanup schedule and/or manually trigger cleanup. Be aware that this only shows you information about (and performs cleanup on) the server you ran the command in.