How do I start a game?
__**1.**__ Create a webhook URL using the command `/%COMMAND_PREFIX%url_manage new` in the channel you want turn notifications sent to, or search for existing ones using `/%COMMAND_PREFIX%url list`
__**2.**__ Before starting a game, every player should start Civilization 6, open **Game Options**, and paste the URL into the **Play By Cloud Webhook URL** field.
__**3.**__ Start a Play By Cloud game with those players.

Once someone has taken the first turn, CivvieBot will get information about the game and the next player. After the configured number of turns, CivvieBot will start sending notifications to that channel when new players' turns are up.

Future games can use the same URL if the same channel needs to be pinged; you don't need to swap it out or create a new one when a game is finished. Just make sure that new games don't use the same name as old ones still being tracked, as that's the only way CivvieBot can differentiate between them. You can always check the list of tracked games using `/%COMMAND_PREFIX%game list`.