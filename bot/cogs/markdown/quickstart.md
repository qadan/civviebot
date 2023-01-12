__**1.**__ In the channel or thread you want to track the game in, use `/%COMMAND_PREFIX%gamemanage add` to add the name of a game I'm allowed to track. This can be the name of a Play By Cloud game in Civilization 6 you're currently part of, or it can be one you plan to create later, as long as you make sure the names match.
__**2.**__ CivvieBot will respond with the webhook URL for the channel or thread. You can also get the URL using `/%COMMAND_PREFIX%url get`.
__**3.**__ Before each player takes their first (or next) turn, they should open **Game Options** and paste the URL into the **Play By Cloud Webhook URL** field.

Once a turn been taken, CivvieBot will get a notification about the game and start tracking it. Each time a turn is taken and it learns about a new player, it'll also start tracking them too.

**NOTE:** CivvieBot doesn't start actually pinging the channel until a certain number of turns have passed; you can set this using `/%COMMAND_PREFIX%gamemanage edit`.