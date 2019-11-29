# CivvieBot

A dead simple app that listens for POST requests from Civilization VI and
converts them to notifications on a Discord server.

## Requirements

- Python 3.6+
- Some installed python modules; check the `requirements.txt` or just install
e'm from there

## Installation

1. Copy `sample.config.yaml` to `config.yaml`.
  * You can either keep this in the root folder for `civviebot`, or you can
    use the `CIVVIEBOT_CONFIG` environment variable to specify your own path
    to the config.
2. Create a Discord webhook. Once you have it, copy the URL into your
`config.yaml` as the `webhook_url`.
3. Run the `civviebot` inside `civviebot.py` in your magical
[WSGI](https://wsgi.readthedocs.io/en/latest/what.html) app of choice. Something
like:

```python
from civviebot import civviebot as application
```

`civviebot.wsgi` is included for Apache integration or whatever. I dunno, try
this for hosting on port `5432`; don't forget to install `mod_wsgi.so`:

```xml
<VirtualHost *:5432>
  WSGIDaemonProcess civviebot user=ubuntu group=ubuntu threads=5
  WSGIScriptAlias / /path/to/civviebot/civviebot.wsgi
  <Directory /path/to/civviebot>
      WSGIProcessGroup civviebot
      WSGIApplicationGroup %{GLOBAL}
      Order deny,allow
      Allow from all
  </Directory>
</VirtualHost>
```

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
- Curious if user objects from Discord can provide Steam account info at all.
That would make mapping super simple.
- Allow for per-game configurations?

## Contact

- [fantallis](https://github.com/qadan)
- fantallis#3161 on Discord

## License

GPL v3
