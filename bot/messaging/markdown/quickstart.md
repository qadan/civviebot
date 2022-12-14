__**1.**__ Try `/%COMMAND_PREFIX%url list` in the channel you want turn notifications sent to; this will tell you if someone has already created a webhook URL in that channel.
__**2.**__ If nothing comes up, or if you just want to have a separate URL for your games, make a new one with `/%COMMAND_PREFIX%url new`.
__**3.**__ Either way, you should now have a URL to copy.
__**4.**__ Before you start a game, every player should start Civilization 6, open **Game Options**, and paste the URL into the **Play By Cloud Webhook URL** field.
__**5.**__ Start a Play By Cloud game with those players.
__**6.**__ Once the first turn has been taken, CivvieBot will get a notification about your game and start tracking it. Each time a turn is taken and it learns about a new player, it'll also start tracking them too.
__**7.**__ Once any of your turns in the game are up, you can use `/%COMMAND_PREFIX%player link` to search for your player name and link it to your Discord account; that way, you'll be pinged properly on future turns.

**NOTE:** CivvieBot doesn't start actually pinging the channel until a certain number of turns have passed. You can set this number of turns when you initially make the URL by setting the `minimum_turns` option, or you can change it after the fact for a URL using `/%COMMAND_PREFIX%url edit`, or you can change it just for one game using `/%COMMAND_PREFIX%game edit`. You can also check it for both the URL and individual games using `/%COMMAND_PREFIX%url info` and `/%COMMAND_PREFIX%game info`.