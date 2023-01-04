# CivvieBot

CivvieBot is a Discord bot and light API that can generate webhook URLs for use with the Cloud Play feature in Civilization 6, and receive turn notifications for those games. Users can also link themselves to tracked players, allowing them to get actual Discord notifications on their turn. The bot includes other slash commands that help keep track of games and players without the need to open Civilization 6.

## @TODO:

* Test with Civ 6 instead of Postman, inspect to see if there's anything we can use to somewhat validate incoming requests as being from Civ 6
* Merge -> 1.0

## Installation

### Creating the app and bot

CivvieBot requires configuration from the app and bot you have set up in Discord. Follow [their setup instructions](https://discord.com/developers/docs/getting-started#creating-an-app) for more details.

### Required configuration

Two environment variables are required to run `civviebot.py`: `DISCORD_CLIENT_ID` and `DISCORD_TOKEN`. Additionally, both `civviebot.py` and `civviebot_api.py` require a configuration to be passed in that will connect them both to a shared database. Check the [environment variables](#environment-variables) and [database configuration](#database-configuration) sections below for details.

### Logging

`logging.yml` (or any logging YAML specified by `LOGGING_CONFIG`) uses the Python logging configuration [dictionary schema](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema); check the documentation for more information.

The default included logging implementation contains a `logging.handlers.RotatingFileHandler` handler that is unused; if you'd like, change the `filename` (or make sure that the given `filename` is writable by CivvieBot) and you can add the `logrotate` handler to whichever loggers you'd like.

### Running the bot

CivvieBot is split into two parts:

* `civviebot.py` is the Discord bot. Running this will activate the bot and have it join Discord.
* `civviebot_api.py` is the API endpoint. It contains `civviebot_api`, which should be run using a [WSGI server](https://wsgi.readthedocs.io/en/latest/servers.html)

If you just want to get it going:

```bash
python3 -m pip install --no-cache-dir -r requirements.txt
nohup python3 -m hypercorn civviebot_api:civviebot_api --bind 127.0.0.1:3002 > civviebot_api.log &
nohup python3 civviebot.py > civviebot.log &
```

### Exposing the bot to port 80 due to issues with Civ 6

Civilization 6 doesn't understand how to make requests to URLs that contain a port number like `:3002`. That's not a joke, it is genuinely that bad. This creates a problem if you're running it on an operating system that restricts the use of low port numbers to specific privileged users. Likely, if you ask a WSGI server to reserve port 80 using an out-of-the-box server configuration, it'll tell you to kindly to stop doing that.

It's up to you to deal with this how you will; the most common solution is to run a reverse proxy through a web server that forwards `:80` traffic to the API.

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
|`CIVVIEBOT_HOST`|The host this app will report that it respond to requests at; used for sending messages containing a full webhook URL. Bear in mind that only `http://` addresses are understood by Civ 6|`string`|localhost|
|`LOGGING_CONFIG`|The location of the logging configuration YAML to use|`path`|`logging.yml`|
|`DOTENV_PATH`|The location of `.env` to pull any of these variables from; omitting will attempt to pull from CivvieBot's root directory|`path`|`null`|


#### Database configuration

Prefixing an environment variable with `CIVVIEBOT_DB_` will pass that parameter on to Pony's [`db.bind`](https://docs.ponyorm.org/database.html#binding-the-database-object-to-a-specific-database) when creating or connecting to the database; for example, `CIVVIEBOT_DB_PROVIDER` would be passed as the `provider` keyword argument. Setting `CIVVIEBOT_DB_FILENAME` will set `create_db` to `True` as well (this is ignored if the file already exists).

**Note**: Using specific databases outside of `sqlite` may require the installation of additional Python modules that are not included in `requirements.txt` - for example, using `mysql` requires the `pymysql` and `cryptography` modules to also be installed.

## Usage

### Adding to a server

If you're familiar with Discord bots, just know that CivvieBot expects the following OAuth2 permissions:

* The `bot` and `application.commands` scopes
* The **Send Messages** and **Read Messages/View Channels** bot permissions
* Optionally, the **Send Messages in Threads** bot permission if you'd like CivvieBot to manage games in threads

Otherwise, once CivvieBot is installed and running, if you open CivvieBot's API in your browser, it'll give you the link and some setup instructions for getting it up and running in a Discord server.

### Getting documentation

Documentation on how to use CivvieBot is provided by CivvieBot itself. Most of the documentation is provided by slash commands, but you can also get some pointers by trying to access the CivvieBot API through a browser.

Once it's set up in a channel, use `/COMMAND_PREFIX quickstart` for a quickstart guide, `/COMMAND_PREFIX faq` for some more specific documentation, or `/COMMAND_PREFIX commands` to list commands and their functions. Replace `COMMAND_PREFIX` with the `COMMAND_PREFIX` you're actually using.

Once you make a webhook URL, if you open it in your browser, it'll give you a bit of direction on how it's intended to be used.

## Contact

- [fantallis](https://github.com/qadan)
- fantallis#3161 on Discord

## License

GPL v3
