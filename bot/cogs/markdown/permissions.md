CivvieBot tracks three different permissions, listed here in the order an administrator sees when using `/%COMMAND_PREFIX permissions`:

__**Player Permissions ("Select roles for players")**__

A basic player with permission to:

* View the FAQ (`/%COMMAND_PREFIX faq`), quickstart guide (`/%COMMAND_PREFIX quickstart`), and command list (`/%COMMAND_PREFIX commands`) - though commands are limited to ones they can use
* List tracked games in a channel (`/%COMMAND_PREFIXgame list`)
* List webhook URLs in a channel (`/%COMMAND_PREFIXurl list`)
* Link themselves to an unlinked player (`/%COMMAND_PREFIXplayer link`, limited to unlinked players)
* Unlink themselves from a player they're linked to (`/%COMMAND_PREFIX unlinkplayer` or `/%COMMAND_PREFIX unlinkuser`, limited to themselves)
* Request what games a player is in (`/%COMMAND_PREFIXplayer games`)
* Request what games a player is up in (`/%COMMAND_PREFIXplayer upin`)

Initially, this is everyone in the server.

__**Game Administrators ("Select roles for Game Administrators")**__

Has all the permissions of a Player, and also has permission to:

* Use this help command (`/%COMMAND_PREFIX list_permissions`)
* Modify tracked games, including editing (`/%COMMAND_PREFIXgame edit`), toggling mute (`/%COMMAND_PREFIXgame toggle_mute`), manually pinging (`/%COMMAND_PREFIXgame ping`), and deleting (`/%COMMAND_PREFIXgame delete`)
* Link any player to any user in a channel (`/%COMMAND_PREFIXplayer link`)
* Unlink any linked users and players (`/%COMMAND_PREFIX unlinkplayer` or `/%COMMAND_PREFIX unlinkuser`)
* Create new webhook URLs (`/%COMMAND_PREFIXurl new`)
* Edit URL configurations (`/%COMMAND_PREFIXurl edit`)
* Move an existing URL to a new channel (`/%COMMAND_PREFIXurl move`)
* Delete a URL (`/%COMMAND_PREFIXurl delete`)

Initially, this is the server's administrative role.

__**Administrators ("Select roles for modifying permissions")**__

Has all the permissions of a Game Administrator, and also has permission to:

* Change what roles are attached to which permissions (`/%COMMAND_PREFIX permissions`)

Initially, this is the server's administrative role.