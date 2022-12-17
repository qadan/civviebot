__**What is CivvieBot?**__

CivvieBot makes use of Civilization 6's Webhook URL support to provide turn notifications for Play By Cloud games directly in a Discord channel.

__**How does it work?**__

In the settings for Civilization 6, you may have noticed a field called **Play By Cloud Webhook URL**. When you finish your turn in a Play By Cloud game, Civilization 6 will send a message to that URL containing information about the new turn. It's essentially just a type of turn notification that a web server can recieve and be configured to understand.

CivvieBot is able to create and manage webhook URLs that understand Civilization 6's turn notification messages. It ties those URLs to the Discord channel they were created in, and sends any notifications it gets from the game to that channel.

__**How do I start a game?**__

__**1.**__ Create a webhook URL using the command `/%COMMAND_PREFIX%url create` in the channel you want turn notifications sent to. This will also let you choose how many turns should pass before the first ping.
__**2.**__ Once you hit the Submit button, CivvieBot will respond with a URL.
__**3.**__ Before starting a game, every player should start Civilization 6, open **Game Options**, and paste the URL into the **Play By Cloud Webhook URL** field.
__**4.**__ Start a Play By Cloud game with those players.
__**5.**__ Once someone has taken the first turn, CivvieBot will get information about the game and the next player.
__**6.**__ After a (configurable) number of turns, CivvieBot will start sending notifications to that channel when new players' turns are up.

Future games can use the same URL if the same channel needs to be pinged; you don't need to swap it out or create a new one when a game is finished. Just make sure that new games don't use the same as old ones still being tracked, as that's the only way CivvieBot can differentiate between them. You can always check the list of tracked games using `/%COMMAND_PREFIX%game list`.

__**What should I set Play By Cloud Webhook Frequency to?**__

It doesn't really matter; CivvieBot will only ping once per new turn anyway. At least if you set it to "My Turn", you won't be pinging CivvieBot more than necessary 🙂

__**How do I get pinged by my @username when it's my turn?**__

CivvieBot doesn't know what your player name is until it gets a turn notification directed at you.

Once it does, CivvieBot allows you to link yourself to that player. When CivvieBot pops a turn notification, you'll see a button under it that says `This is me`. Clicking on that button will link the player and your Discord ID, so when it's your turn again, it'll ping you directly instead.

If your turn passed a while ago, or if you need to link someone else, use `/%COMMAND_PREFIXplayer link`.

__**How do I remove a link between a player and a Discord user?**__

You can always click or re-click the link button on a notification if it's recent enough. Otherwise, you can use one of either `/%COMMAND_PREFIX%player unlinkplayer` or `/%COMMAND_PREFIX%player unlinkuser` to search for a link to remove by player or Discord user.

The link will be maintained for future games using the same URL.

__**How many games can I track in a channel?**__

CivvieBot tracks 25 games at a time per-channel. After this, new games simply won't be tracked. If CivvieBot is in constant use, consider cleaning up games when they're done using `/%COMMAND_PREFIX%game delete` instead of waiting for the automatic cleanup, or simply use multiple channels.

__**Anything else I should know?**__

Not really, if you're just playing a game. However, there are a bunch of other commands that you and/or Discord mods can use to change the settings of URLs, tracked games, and tracked players. Use `/%COMMAND_PREFIX% commands` for more information.