CivvieBot didn't ping; what do I do?
There are a few reasons this can happen:

* The current turn in the game is lower than the minimum turn I ping at. I don't start pinging in Discord until a certain number of turns have passed; it helps make sure the start of a game isn't just constant pings. You can check this using `/%COMMAND_PREFIX%game info`, or edit it using `/%COMMAND_PREFIX%game_manage edit`.
* I simply didn't get the notification from Civilization 6. This can happen for a lot of reasons; the game can be a little unreliable. If this is the case, you might have to wait for a new turn before I send another ping.
* You tried to start a new game, but the URL you have configured already has 25 games attached to it. When 25 games are being tracked via a URL, I stop letting it track new ones; you'll have to either wait for some to be cleaned up automatically, or manual cleanup can be run using `/%COMMAND_PREFIX%game_manage delete`.

You can always ping or re-ping the current turn using `/%COMMAND_PREFIX%game_manage ping`.