
CREATE TABLE player_games (
	slug VARCHAR(16) NOT NULL, 
	playerid INTEGER NOT NULL, 
	gameid INTEGER NOT NULL, 
	PRIMARY KEY (slug, playerid, gameid), 
	FOREIGN KEY(slug) REFERENCES webhook_url (slug), 
	FOREIGN KEY(playerid) REFERENCES player (id), 
	FOREIGN KEY(gameid) REFERENCES game (id)
)

