What exactly do you track about me/my server?
These are the most important things I track with reference to your privacy:

* Webhook URLs are tied to a Discord channel's snowflake. I don't store any information about a server other than these.
* I keep a record of each player and game by the reported names that I get from Civilization 6.
* When someone links a player to a Discord user, I add the Discord user's snowflake to the player record.

**What do you mean by "snowflake"?**

Snowflakes are special numbers assigned to different things around Discord that uniquely identify them, like a user or a channel. They're not called IDs because they're more than just a uniquely identifying number; they also contain another couple of pieces of information, most importantly the exact time that user or channel was created.

That being said, Discord snowflakes _are_ public information (to an extent); if you can see something on Discord, you can see its snowflake, and therefore know when it was created, so I'm not ever hanging onto anything people aren't already privy to.

Discord has a little more information about snowflakes if you'd like to peruse a rather dry reference manual: https://discord.com/developers/docs/reference#snowflakes

**How long do you hang onto information, and how do I get rid of it?**

* I hang onto webhook URLs as long as I'm in the server they're attached to. While I'm in that server, URLs have to be removed manually using `/%COMMAND_PREFIX%url_manage delete`. When they are deleted, associated games and players are also removed. If I'm removed from a server, I flag webhook URLs, as well as their attached games and players, to be deleted during automatic cleanup.
* I hang onto games as long as they're active - meaning as long as they haven't been automatically cleaned up. Individual games can be manually removed using `/%COMMAND_PREFIX%game_manage delete`.
* I hang onto players as long as they're part of at least one active game. Once the last game they're part of is deleted, they get deleted too.
* I hang onto a player's linked Discord snowflake for as long as I hang onto the player - but that can be removed at any time using `/%COMMAND_PREFIX%self unlink` or `/%COMMAND_PREFIX%player_manage unlinkplayer`, or using the unlink button on that player's turn.

Use `/%COMMAND_PREFIX%game_manage cleanup` to get information about the cleanup schedule and/or manually trigger cleanup. Be aware that this only shows you information about (and performs cleanup on) the server you ran the command in.