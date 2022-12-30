How does it work?
In the settings for Civilization 6, you may have noticed a field called **Play By Cloud Webhook URL**. When you finish your turn in a Play By Cloud game, Civilization 6 will send a message to that URL containing information about the new turn. It's essentially just a type of turn notification that a web server can recieve and be configured to understand.

In addition to being a Discord bot, I'm also a web server configured to understand those messages. I'm able to create and manage webhook URLs that Civilization 6 can send those messages to. I tie those URLs to the Discord channel they were created in, and send any notifications I get from the game to that channel.

Because I'm tracking more information than just turns, I can also provide a little bit of information about active games and players without you having to hop into Civilization 6.