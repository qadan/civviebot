__**1.**__ Try `/%COMMAND_PREFIX%url list` in the channel you want turn notifications sent to; this will tell you if someone has already created a webhook URL in that channel.
__**2.**__ If nothing comes up, or if you just want to have a separate URL for your games, make a new one with `/%COMMAND_PREFIX%url_manage new`.
__**3.**__ Either way, before you start a game, every player should start Civilization 6, open **Game Options**, and paste the URL into the **Play By Cloud Webhook URL** field.
__**4.**__ Start a Play By Cloud game with those players. Players need to be connected to 2KGames to use Play By Cloud; this link is generally managed by the platform you're playing on (e.g., Steam)

Once the first turn has been taken, CivvieBot will get a notification about your game and start tracking it. Each time a turn is taken and it learns about a new player, it'll also start tracking them too.

**NOTE:** CivvieBot doesn't start actually pinging the channel until a certain number of turns have passed. You can set this number of turns when you initially make the URL by setting the `minimum_turns` option or you can change it after the fact for URLs and individual games. Check `/%COMMAND_PREFIX% commands` for more info.