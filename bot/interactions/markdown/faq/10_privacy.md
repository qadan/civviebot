What exactly do you track about me/this server?
These are the most important things I track with reference to your privacy:

* The first time I have to provide a URL for a channel, I generate one and tie it to that channel's snowflake. I don't store any information about a server other than these snowflakes.
* I keep a record of each player by the reported name that I get from Civilization 6; these are tied to the channel's snowflake.
* When someone links a player to a Discord user, I add the Discord user's snowflake to the player record.

**What do you mean by "snowflake"?**

Discord uses Twitter-style snowflakes - numbers that uniquely identify something in the app like a user or a channel. They're a little more involved than a simple ID; they also contain another couple of pieces of information, like the exact time that user or channel or whatever was created.

That being said, Discord snowflakes _are_ public information (to an extent); if you can see something on Discord, you can see its snowflake, so I'm not ever hanging onto anything that someone who can see it isn't already privy to.

Discord has a little more information about snowflakes if you'd like to peruse a rather dry reference manual: https://discord.com/developers/docs/reference#snowflakes

Everything I do, from notifications to autocompletes, is directly tied to the snowflake of the channel it came from.

**How long do you hang onto information, and how do I get rid of it?**

* I hang onto webhook URLs as long as I'm in the channel they're attached to. If I'm removed from a channel, the URL and any attached games, players, and tracked notifications are removed.
* I hang onto games as long as they're active - meaning as long as they haven't been automatically cleaned up or I'm removed from the game's channel. Individual games can be manually removed using `/%COMMAND_PREFIX%tracking delete`.
* I hang on to tracked players as long as I'm in the channel that player was tracked in. I do this to ensure users don't have to repeatedly link themselves to the same player over and over for each new game.
* I hang onto a player's linked Discord snowflake for as long as I hang onto the player - but that can be removed at any time using `/%COMMAND_PREFIX%self unlink` or `/%COMMAND_PREFIX%player unlink`, or using the unlink button on that player's turn.

Removing a channel removes all of the data I have stored for it. This is why it's generally best to run games in threads; it makes cleanup easy without causing problems in the rest of the server.

Use `/%COMMAND_PREFIX%tracking cleanup` to get information about the cleanup schedule and/or manually trigger cleanup. Be aware that this only shows you information about (and performs cleanup on) the server you ran the command in.