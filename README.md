# CivvieBot

CivvieBot is a Discord bot that can generate Webhook URLs for use with the Cloud Play feature in Civilization 6. Users paste the URL into the settings for Civilization 6, and the bot then pings turn notifications from those players' Cloud Play games in the channel it was created in. Users in that channel can also link themselves to players in the game, allowing them to get actual notifications by their Discord account instead of just their in-game player name.

## @TODO:

* Test the current list of commands
* Add in optional role limitations
* Test with Civ 6 instead of Postman
* Complete README
* `/c6 commands` should only display commands the user can use.

## Installation

Copy sample.config.yml to config.yml and fill in the `discord_client_id`, `discord_client_secret`, and `discord_token`. Change the `app_url` and `port` as well, if necessary.

## Usage

```bash
pipenv install
pipenv run civviebot
```

CivvieBot interprets two environment variables as well:

* `CIVVIEBOT_CONFIG` - the full path to `config.yml`; defaults to the same folder the root `civviebot.py` is in.
* `CIVVIEBOT_PATH` - the full path to all of the files configured in the `path` section of `config.yml`.

## Documentation

Documentation on how to use CivvieBot is provided by CivvieBot itself. Once it's up and running in a channel, 

## Contact

- [fantallis](https://github.com/qadan)
- fantallis#3161 on Discord

## License

GPL v3
