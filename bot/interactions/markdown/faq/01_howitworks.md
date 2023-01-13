How does it work?
I make use of the **Play By Cloud Webhook URL** in the settings for Civilization 6. When you finish your turn in a Play By Cloud game, Civilization 6 will send a message to that URL containing information about the new turn. It's essentially just a type of turn notification that a web server can recieve and be configured to understand.

I'm able to create and manage webhook URLs that Civilization 6 can send those messages to. If someone tells me the name of a Play By Cloud game in a channel (or thread!), I make a webhook URL that ties notifications for that game to that channel, and I pass along any notifications I get from the game to that channel.

I'm also able to maintain links between players that I know about in a channel and users in that channel; that way, users can assert which player they are so I can ping them directly when it's their turn.

Because I'm tracking more information than just turns, I can also provide a little bit of information about active games and players without you having to hop into Civilization 6.