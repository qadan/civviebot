# CivvieBot

CivvieBot is a Discord bot that can generate Webhook URLs for use with the Cloud Play feature in Civilization 6. Users paste the URL into the settings for Civilization 6, and the bot then pings turn notifications from those players' Cloud Play games in the channel it was created in. Users in that channel can also link themselves to players in the game, allowing them to get actual notifications by their Discord account instead of just their in-game player name.

## @TODO:

* Finish the API's ability to run on not-local
* Test the current list of commands
* Test the current list of commands when the db is empty
* Test with Civ 6 instead of Postman, inspect to see if there's anything we can use to somewhat validate incoming requests as being from Civ 6
* Complete README
* Lint
* Merge -> 1.0

## Installation

### Creating the app and bot

CivvieBot requires configuration from the app and bot you have set up in Discord. Follow [their setup instructions](https://discord.com/developers/docs/getting-started#creating-an-app) for more details.

### Configuration

Once you have the app and bot set up, copy `sample.config.yml` to `config.yml` and fill in the `discord_client_id`, `discord_client_secret`, and `discord_token`. Change the `host` and `port` as well, if necessary.

Getting the first three pieces of configuration involves creating an app and establishing a bot in Discord; 

The other two pieces of configuration default to `localhost` and `3002`, respectively, and should be changed accordingly if you're installing CivvieBot on a public server.

### Logging

Some basic default logging is established in `logging.yml` that outputs to the console:

* A `civviebot` logger for the bot and API
* A `discord` logger for messaging from `py-cord`

If the log level for `civviebot` is effectively seen as `DEBUG`, debug mode for Quart will also be enabled.

`logging.yml` uses the Python logging configuration [dictionary schema](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema); check the documentation for more information.

### Running the bot

```bash
pipenv install
pipenv run civviebot
```

CivvieBot interprets two environment variables as well:

* `CIVVIEBOT_CONFIG` - the full path to `config.yml`; defaults to the same folder the root `civviebot.py` is in.
* `CIVVIEBOT_PATH` - the full path to all of the files configured in the `path` section of `config.yml`.

## Usage

Documentation on how to use CivvieBot is provided by CivvieBot itself. Most of the documentation is provided by slash commands, but you can also get some pointers by trying to access the CivvieBot API through a browser.

### Adding to a server

If you're familiar with Discord bots, just know that CivvieBot expects the following OAuth2 permissions:

* The `bot` and `application.commands` scopes
* The **Send Messages** and **Read Messages/View Channels** bot permissions
* Optionally, the **Send Messages in Threads** bot permission if you'd like CivvieBot to manage games in threads

Otherwise, once CivvieBot is installed and running, if you open CivvieBot's API in your browser (i.e., wherever your `host` and `port` are configured), it'll give you the link and some setup instructions for getting it up and running in a Discord server.

### Getting documentation

Once it's set up in a channel, use `/COMMAND_PREFIX faq` for some base documentation, or `/COMMAND_PREFIX commands` to list commands and their function, replacing `COMMAND_PREFIX` with your configured `command_prefix` in `config.yml`.

Once you make a webhook URL, if you open it in your browser, it'll give you a bit of direction on how it's intended to be used.

## Contact

- [fantallis](https://github.com/qadan)
- fantallis#3161 on Discord

## License

GPL v3
