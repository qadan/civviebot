__**What is CivvieBot?**__

CivvieBot makes use of Civilization 6's Webhook URL support to provide turn notifications for Play By Cloud games directly in a Discord channel.

__**Huh?**__

In the settings for Civilization 6, you may have noticed a field called **Play By Cloud Webhook URL**. When you finish your turn in a Play By Cloud game, Civilization 6 will send a message to that URL containing information about the new turn. It's essentially just a turn notification that a web server can recieve and be configured to understand.

CivvieBot is able to create and manage webhook URLs that understand Civilization 6's turn notification messages. It ties those URLs to the Discord channel they were created in, and sends any notifications it gets from the game to that channel.

__**How do I start a game?**__

__**1.**__ Create a webhook URL using the command `/%COMMAND_PREFIX%url create` in the channel you want turn notifications sent to.
__**2.**__ CivvieBot will respond with a URL.
__**3.**__ Every player should start Civilization 6, open **Game Options**, and paste the URL into the **Play By Cloud Webhook URL** field.
__**4.**__ Start a Play By Cloud game with those players.
__**5.**__ Once someone has taken the first turn, CivvieBot will get information about the game and the next player.
__**6.**__ After a (configurable) number of turns, CivvieBot will start sending notifications to that channel when new players' turns are up.

Future games can use the same URL if the same channel needs to be pinged; you don't need to swap it out or create a new one when a game is finished. Just make sure that the games all have unique names, as that's the only way CivvieBot can differentiate between them.

__**How do I get pinged in Discord when it's my turn?**__

Civilization 6 does not, of course, know what your Discord ID is, or even that Discord exists. And CivvieBot doesn't even know what your player name is until it gets a turn notification directed at you.

However, once it does get a turn notification for a specific player, CivvieBot allows you to link a Discord user to that player. When CivvieBot pops a turn notification, you'll see a button under it that says `This is me`. Clicking on that button will link the player and your Discord ID, so when it's your turn again, it'll ping you directly instead.

That link can also be removed after the fact, either by re-clicking the button, or by clicking it on a future notification.

__**Anything else I should know?**__

Not really, if you're just playing a game. However, there are a bunch of commands that you and/or Discord mods can use to change the settings of URLs, tracked games, and tracked players. Use `/%COMMAND_PREFIX% commands` for more information.

And a quick note for those administrators using those commands: CivvieBot will track a maximum of 25 games at a time per-channel. After this, new games won't be tracked. If CivvieBot is in constant use, consider cleaning up games when they're done instead of waiting for the automatic cleanup, or simply use multiple channels.