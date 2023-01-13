CivvieBot didn't ping; what do I do?
There are a couple of reasons this can happen:

* The current turn in the game is lower than the minimum turn I ping at. I don't start pinging in Discord until a certain number of turns have passed; it helps make sure the start of a game isn't just constant pings before it goes async. You can check this using `/%COMMAND_PREFIX%game info`, or edit it using `/%COMMAND_PREFIX%gamemanage edit`.
* I simply didn't get the notification from Civilization 6. This can happen for a lot of reasons; the game can be a little unreliable. If this is the case, you might have to wait for a new turn before I send another ping.

You can always ping or re-ping the current turn using `/%COMMAND_PREFIX%gamemanage ping`.