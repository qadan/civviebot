I was warned about a "duplicate game", what should I do?
In this case, you want to either:

* Restart the new game under a different name, or
* Use `%COMMAND_PREFIX%game_manage delete` to remove the existing game if it's done, or
* Wait for the game to automatically get cleaned up

This happens when I get a notification from Civilization 6 about a game I'm already tracking - or at least one with the exact same name, sent to the exact same webhook URL - but the turn number in the notification is lower than the current turn in the game I already know about. This likely means that someone started a game with the same name as the one still being tracked.

**How come you operate like this?**

The problem is, I don't get any information from Civilization 6 I can use to uniquely identify a game and make sure I'm tracking the right one. I just get the name of the game, the name of the player who's up, and the current turn number. I can't even really know all of the players in a game for certain, or what turn it really is, because I rely completely on the players themselves self-reporting (and not trying to trick me). So I can only make a "best effort" guess about what I'm tracking.

Tying games to unique webhook URLs is how I combat this problem. I can at least know that each game tied to a URL has a unique name.