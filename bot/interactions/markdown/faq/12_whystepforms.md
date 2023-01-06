How come I have to pick games/URLs after I type the command?
It has to do with how Discord slash commands work; it's still fairly fresh and I'm waiting on a couple of key features.

**How come you don't use a list of options in the command?**

Because the list of options for a slash command has to be provided when I register the command. I can't provide different options for slash commands dynamically, so select menus with games and players and timers and "who's currently up" and other information is just a no-go unless it's part of a message.

**Why not use an autocomplete?**

Like any database, I actually look up games and players and URLs by unique numbers, not the name of the game/player itself. I could let people type in the name of a game, but at the end of the day, I need to know the actual number of that game in the database. Because Discord autocomplete can only work with what you're typing, that number would have to be included in what you type, meaning you'd either have to know that number offhand, or I'd have to provide it to you and force you to send it back to me as part of the autocomplete result, or I'd have to do some other shenanigans to try to tie what you're typing to the number. All of these, I think, are worse options than just letting you pick it from a follow-up message.