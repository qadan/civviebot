# CivvieBot

CivvieBot is a Discord bot that can generate webhook URLs for use with the Cloud Play feature in Civilization 6. Adding a URL to the settings for Civilization 6 allows CivvieBot to track Cloud Play games and their players, and send turn notifications. Users can also link themselves to tracked players, allowing them to get actual Discord notifications on their turn.

## @TODO:

* Test with Civ 6 instead of Postman, inspect to see if there's anything we can use to somewhat validate incoming requests as being from Civ 6
* Merge -> 1.0

## Installation

### Creating the app and bot

CivvieBot requires configuration from the app and bot you have set up in Discord. Follow [their setup instructions](https://discord.com/developers/docs/getting-started#creating-an-app) for more details.

### Configuration

Two environment variables are required to run the bot: `DISCORD_CLIENT_ID` and `DISCORD_TOKEN`. Check the [Environment variables](#environment-variables) section below for details.

### Logging

Some basic default logging is established in `logging.yml` that outputs to the console:

* A `civviebot` logger for the bot and API
* A `discord` logger for messaging from `py-cord`

If the log level for `civviebot` is effectively seen as `DEBUG`, debug mode for Quart will also be enabled.

`logging.yml` uses the Python logging configuration [dictionary schema](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema); check the documentation for more information.

### Running the bot

```bash
python3 -m pip install --no-cache-dir -r requirements.txt
python3 -m hypercorn civviebot_api:civviebot_api --host 0.0.0.0 --port 3002
```

Or really, via Docker:

```bash
docker build https://github.com/qadan/civviebot.git --tag civviebot
docker run -p 80:3002 civviebot
```

### Environment variables

CivvieBot interprets the following environment variables:

|Variable name|Description|Interpreted as|Default|
|-------------|-----------|--------------|-------|
|`DISCORD_CLIENT_ID`|The Client ID of the Discord application containing the bot you intend to act as CivvieBot. You can find this on [the application page](https://discord.com/developers/applications) for your application, then under **OAuth2** on the sidebar|`integer`|**REQUIRED**|
|`DISCORD_TOKEN`|The token of the bot you intend to act as CivvieBot. You can find this on [the application page](https://discord.com/developers/applications) as well, under **Bot** on the sidebar. You'll have to make a bot if you haven't already, and if you don't know the token, you'll be required to reset it as well|`string`|**REQUIRED**|
|`COMMAND_PREFIX`|The slash command prefix CivvieBot commands will use; e.g., c6 to create commands grouped like /c6url and /c6player|`string`|c6|
|`MIN_TURNS`|When a URL is created, `MIN_TURNS` will be used as the number of turns that must pass in a game before notification messages are actually sent. This can be set to something different when a URL is created, or changed for URLs and games after the fact|`integer`|10|
|`NOTIFY_INTERVAL`|How frequent the bot should check the database for new notifications to be sent, in seconds|`float`|5.0|
|`STALE_NOTIFY_INTERVAL`|When a URL is created, `STALE_NOTIFY_INTERVAL` will be used as the maximum number of seconds that should elapse between turns before its games re-ping folks|`float`|604800.0 (one week)|
|`STALE_GAME_LENGTH`|How old, in seconds, the last turn notification should be before a game is considered stale and should be cleaned up|`float`|2592000 (30 days)|
|`NOTIFY_LIMIT`|For new turns and re-pings, the maximum number of each to send out every `NOTIFY_INTERVAL`|`integer`|100|
|`CLEANUP_INTERVAL`|How frequent the bot should run cleanup on the database, in seconds|`float`|86400.0 (24 hours)|
|`CLEANUP_LIMIT`|How many of each game, player, and webhook URL should be deleted every `CLEANUP_INTERVAL`|`integer`|1000|
|`DEBUG_GUILD`|A debug guild to use; leave this empty if not debugging|`integer`|`null`|
|`CIVVIEBOT_HOST`|The host this app will respond to requests at; this is only really used for sending messages containing a full webhook URL. Bear in mind that only `http://` addresses are understood by Civ 6|`string`|localhost|
|`LOGGING_CONFIG`|The location of the logging configuration YAML to use|`path`|`logging.yml`|
|`DOTENV_PATH`|The location of `.env` to pull any of these variables from; omitting will attempt to pull from CivvieBot's root directory|`path`|`null`|

Additionally, prefixing an environment variable with `CIVVIEBOT_DB_` will pass that parameter on to Pony's [`db.bind`](https://docs.ponyorm.org/database.html#binding-the-database-object-to-a-specific-database) when creating or connecting to the database; for example, `CIVVIEBOT_DB_PROVIDER` would be passed as the `provider` keyword argument. Setting `CIVVIEBOT_DB_FILENAME` will set `create_db` to `True` as well (this is ignored if the file already exists).

CivvieBot also checks for the existence of a `.env` file to pull variables from.

## Usage

Documentation on how to use CivvieBot is provided by CivvieBot itself. Most of the documentation is provided by slash commands, but you can also get some pointers by trying to access the CivvieBot API through a browser.

### Adding to a server

If you're familiar with Discord bots, just know that CivvieBot expects the following OAuth2 permissions:

* The `bot` and `application.commands` scopes
* The **Send Messages** and **Read Messages/View Channels** bot permissions
* Optionally, the **Send Messages in Threads** bot permission if you'd like CivvieBot to manage games in threads

Otherwise, once CivvieBot is installed and running, if you open CivvieBot's API in your browser, it'll give you the link and some setup instructions for getting it up and running in a Discord server.

### Getting documentation

Once it's set up in a channel, use `/COMMAND_PREFIX faq` for some base documentation, or `/COMMAND_PREFIX commands` to list commands and their function, replacing `COMMAND_PREFIX` with your environment `COMMAND_PREFIX`.

Once you make a webhook URL, if you open it in your browser, it'll give you a bit of direction on how it's intended to be used.

## Contact

- [fantallis](https://github.com/qadan)
- fantallis#3161 on Discord

## License

GPL v3
