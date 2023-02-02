__**1.**__ Use `/%COMMAND_PREFIX%tracking add` to add the name of a game for me to track. This can be the name of a Play By Cloud game in Civilization 6 you're currently part of, or it can be one you plan to create later, as long as you make sure the name you give me is the same one you make in the game.
__**2.**__ I'll respond with the webhook URL for the channel or thread. You can also get it at any time with `/%COMMAND_PREFIX%url get`.
__**3.**__ Before each player takes their first (or next) turn in Civilization 6, they should open **Game Options** and paste the URL into the **Play By Cloud Webhook URL** field. The other settings are fine as-is.

Once a turn been taken, I'll get a notification about the game and start tracking it. Each time a turn is taken, if I get a notification for a player I don't know about, I'll start tracking them too.

**NOTE:** I don't start actually pinging until a certain number of turns have passed; you can see this using `/%COMMAND_PREFIX%game info` and change it using `/%COMMAND_PREFIX%tracking edit`. I still track information I get from Civilization 6, though, so you can see that at any time.