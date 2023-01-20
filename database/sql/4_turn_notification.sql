
CREATE TABLE turn_notification (
	turn INTEGER NOT NULL, 
	playerid INTEGER NOT NULL, 
	gameid INTEGER NOT NULL, 
	slug VARCHAR(16) NOT NULL, 
	logtime TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	lastnotified TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (turn, playerid, gameid, slug), 
	FOREIGN KEY(playerid) REFERENCES player (id), 
	FOREIGN KEY(gameid) REFERENCES game (id), 
	FOREIGN KEY(slug) REFERENCES webhook_url (slug)
)

