I was warned about a "duplicate game", what should I do?
This means I got a notification from Civilization 6 about a game I'm already tracking, but the turn number in the notification is lower than the current turn in the game I already know about. This likely means that someone started a game with the same name as the one still being tracked, and I can't really deal with that.

In this case, you want to either:

* Restart the new game under a different name, or
* Use `/%COMMAND_PREFIX%tracking delete` to remove the existing game if it's done, or
* If the game has been inactive past the maximum inactivity period, you can either wait for me to automatically remove it, or someone with permission can run cleanup using `/%COMMAND_PREFIX%tracking cleanup`

**How come you can't deal with it?**

The problem is, I don't get any information from Civilization 6 I can use to make sure I'm tracking the right game. I rely completely on players themselves self-reporting. So I can only make a "best effort" guess about what I'm tracking.

I combat this problem by tying game names and URLs together, and tying those URLs to Discord channels. This has the knock-on effect of making it so that I can't have two games in a channel with the same name - I wouldn't be able to tell them apart, and I'd end up lumping all the notifications together. Instead, I just don't track notifications if I detect they're from a duplicate game, and opt to warn you about the issue.