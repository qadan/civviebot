# CivvieBot

CivvieBot is a Discord bot and light API that generates webhook URLs for use with the Cloud Play feature in Civilization 6. Users can add games to a channel, and CivvieBot will forward turn notifications for those games straight to Discord. Users can also link themselves to tracked players, allowing them to get actual Discord notifications on their turn. The bot includes other slash commands that help keep track of games and players without the need to open Civilization 6.

## @TODO:

* Test with Civ 6 instead of Postman, inspect to see if there's anything we can use to somewhat validate incoming requests as being from Civ 6
* Merge -> 1.0

## Installation

CivvieBot is comprised of three parts:

* A database for stashing game tracking information
* `civviebot_api.py` is the API; it listens to requests from Civilization 6 and stashes them in the database
* `civviebot.py` is the Discord bot; it forwards notifications to channels, allows users to check tracked game information (e.g., who's up, which users are linked to which players, etc.), and allows users to change how player links and notifications work

### 1. Creating the app and bot on the Discord side

Configuring CivvieBot will require ID and token information from the app and bot you have set up in Discord. If you haven't set up an app or bot, follow [their setup instructions](https://discord.com/developers/docs/getting-started#creating-an-app) for more details.

### 2. Establishing requirements

CivvieBot requires:

* Python 3.9 or greater
* A WSGI server module to be installed
* Database software [compatible with SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/index.html), containing a database and credentials CivvieBot can read from and write to

CivvieBot is configured using environment variables. Check the [environment variables](#environment-variables) section below for details. However, each part of CivvieBot has required configuration:

* `civviebot.py` requires `DISCORD_TOKEN` for the bot you have set up in Discord and `CIVVIEBOT_HOST` to know how to provide webhook URLs
* `civviebot_api.py` needs the `DISCORD_CLIENT_ID` to tell users how to add the bot to their server
* The shared database requires a database configuration and may require additional Python modules to be installed; check the [database configuration](#database-configuration) sections below for details

### 3. Configuration

CivvieBot uses environment variables to establish configuration. The use of a `.env` file is recommended; check the `DOTENV_PATH` below for more information.

CivvieBot interprets configuration from following environment variables:

|Variable name|Description|Interpreted as|Default|
|-------------|-----------|--------------|-------|
|`CIVVIEBOT_DB_DIALECT`|See [Database configuration](#database-configuration) below|`string`|`mysql`|
|`CIVVIEBOT_DB_DRIVER`|See [Database configuration](#database-configuration) below|`string`|`pymysql`|
|`CIVVIEBOT_DB_URL_*`|See [Database configuration](#database-configuration) below|`strings`|**REQUIRED**|
|`CIVVIEBOT_HOST`|The host this app will report that it respond to requests at; used for sending messages containing a full webhook URL. Bear in mind that only `http://` addresses are understood by Civ 6|`string`|localhost|
|`CLEANUP_INTERVAL`|How frequent the bot should run cleanup on the database, in seconds|`integer`|86400 (24 hours)|
|`CLEANUP_LIMIT`|How many of each game, player, and webhook URL should be deleted every `CLEANUP_INTERVAL`|`integer`|1000|
|`COMMAND_PREFIX`|The slash command prefix CivvieBot commands will use; e.g., c6 to create commands grouped like `/c6url` and `/c6player`|`string`|c6|
|`DEBUG_GUILD`|A debug guild to use; leave this empty if not debugging|`integer`|`null`|
|`DISCORD_CLIENT_ID`|The Client ID of the Discord application containing the bot you intend to act as CivvieBot. You can find this on [the application page](https://discord.com/developers/applications) for your application, then under **OAuth2** on the sidebar|`integer`|**REQUIRED**|
|`DISCORD_TOKEN`|The token of the Discord bot user you intend to act as CivvieBot. You can find this on [the application page](https://discord.com/developers/applications) as well, under **Bot** on the sidebar. You'll have to make a bot if you haven't already, and if you don't know the token, you'll be required to reset it|`string`|**REQUIRED**|
|`DOTENV_PATH`|The location of `.env` to pull any of the following variables from; omitting will attempt to pull from CivvieBot's root directory|`path`|`null`|
|`LOGGING_CONFIG`|The location of the logging configuration YAML to use|`path`|`logging.yml`|
|`MIN_TURNS`|The default number of turns that must pass in a game before notification messages are actually sent. Users can edit this for individual games|`integer`|10|
|`NOTIFY_INTERVAL`|How frequent the bot should check the database for new notifications to be sent, in seconds|`integer`|5|
|`NOTIFY_LIMIT`|For new turns and re-pings, the maximum number of each to send out every `NOTIFY_INTERVAL`|`integer`|100|
|`REMIND_INTERVAL`|The default maximum number of seconds that should elapse between turns in a game before it sends out a reminder ping. Users can edit this for individual games|`integer`|604800 (one week)|
|`SIMPLIFIED_NAMES`|Rather than using the full Discord display name of users, display names as Discord `username#discriminator`|`boolean`|`true`|
|`STALE_GAME_LENGTH`|How old, in seconds, the last turn notification should be before a game is considered 'stale' and should be removed during the bot's regular cleanup|`integer`|2592000 (30 days)|

#### Database configuration

The database requires two environment variables to be set, `CIVVIEBOT_DB_DIALECT` and `CIVVIEBOT_DB_DRIVER`. These equate to valid SQLAlchemy [dialects](https://docs.sqlalchemy.org/en/20/dialects/) and a valid [DBAPI](https://docs.sqlalchemy.org/en/20/glossary.html#term-DBAPI) driver (e.g., the defaults `mysql` and `pymysql` respectively).

Additionally, CivvieBot needs to know what database it's connecting to, and how to do so. Prefixing an environment variable with `CIVVIEBOT_DB_URL_` will pass that parameter on to SQLAlchemy when [generating the database URL](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls) to connect to. For example:

```
CIVVIEBOT_DB_DIALECT=mysql
CIVVIEBOT_DB_DRIVER=pymysql
CIVVIEBOT_DB_URL_USERNAME=civviebot
CIVVIEBOT_DB_URL_PASSWORD=civviebot
CIVVIEBOT_DB_URL_DATABASE=civviebot
CIVVIEBOT_DB_URL_HOST=localhost
CIVVIEBOT_DB_URL_PORT=3306
```

would translate to a database URL of `mysql+pymysql://civviebot:civviebot@localhost:3306/civviebot`

**Note**: `requirements.txt` does not install any database-related modules; this should be done manually.

#### Logging configuration

`logging.yml` (or any logging YAML specified by `LOGGING_CONFIG`) uses the Python logging configuration [dictionary schema](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema); check the documentation for more information.

### 4. Exposing the bot to port 80

Civilization 6 can't send requests to URLs that contain a port number, so the API will need to respond on port 80. With basically any operating system, if you ask a WSGI server to reserve port 80, it'll tell you to kindly to stop doing that.

It's up to you to deal with this how you will; the most common solution is to run a reverse proxy through a web server that forwards port 80 traffic to the API. However, this guide will not make any specific recommendations for deployment beyond saying don't run it as the root user.

## Usage

### Running the bot

* `civviebot.py` can simply be run using Python 3; this will activate the bot and have it join Discord.
* `civviebot_api.py` contains `civviebot_api`, which should be run using a [WSGI server](https://wsgi.readthedocs.io/en/latest/servers.html)

If you just want to get it going, assuming Python 3 and pip3 are installed and you've placed a `.env` containing your config in the base CivvieBot folder:

```bash
# Optionally, generate a virtual environment to work in
python3 -m pip install venv
python3 -m venv venv
./venv/bin/activate
# Install base requirements
python3 -m pip install --no-cache-dir -r requirements.txt
# Install any extra database-required modules and a WSGI server here, e.g., pymysql and gunicorn
python3 -m pip install --no-cache-dir pymysql gunicorn
# Example spinning up both the bot and API with gunicorn on port 3002
nohup python3 -m gunicorn 'civviebot_api:civviebot_api' -b 127.0.0.1:3002 >> civviebot_api.log 2>&1
nohup python3 civviebot.py >> civviebot.log 2>&1
```
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
