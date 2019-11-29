# CivvieBot

A dead simple app that listens for POST requests from Civilization VI and
converts them to notifications on a Discord server.

## Installation

1. Copy `sample.config.yaml` to `config.yaml`.
2. Create a Discord webhook. Once you have it, copy the URL into your `config.yaml`
3. Run the `app` inside `civviebot.py` in your magical [WSGI](https://wsgi.readthedocs.io/en/latest/what.html) app of choice. Something like:

```python
from civviebot import app as application
```

`civviebot.wsgi` is included for Apache integration or whatever.

## Configuration

There's a few other things in `config.yml` you might want to change.

If you want people to get pinged properly, you'll need to fill out the
`user_map` of Steam users to Discord user IDs. Getting the ID kind of stinks as
far as I can tell; the only way is to enable developer mode (App Settings ->
Appearance), then right-click a user ID and click "Copy ID".

Add more messaging capabilities in the `phrases` section. The bot randomly
chooses one to send.

## TODO

- The User ID thing could be made easier, perhaps in a couple different ways ...
would require upgrading this to a fully fledged bot with user privileges. Bleh

## Contact

- [fantallis](https://github.com/qadan)
- fantallis#3161 on Discord

## License

GPL v3
