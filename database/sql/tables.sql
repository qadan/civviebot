CREATE TABLE webhook_url (
	slug VARCHAR(16) NOT NULL,
	channelid BIGINT NOT NULL,
	PRIMARY KEY (slug),
	UNIQUE (channelid)
);

CREATE TABLE game (
	id SERIAL NOT NULL,
	muted BOOLEAN NOT NULL,
	duplicatewarned BOOLEAN,
	remindinterval INTEGER NOT NULL,
	nextremind TIMESTAMP WITHOUT TIME ZONE,
	minturns INTEGER NOT NULL,
	name VARCHAR(255) NOT NULL,
	slug VARCHAR(16) NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT game_to_slug UNIQUE (name, slug),
	FOREIGN KEY(slug) REFERENCES webhook_url (slug)
);

CREATE TABLE player (
	id SERIAL NOT NULL,
	discordid BIGINT,
	name VARCHAR(255) NOT NULL,
	slug VARCHAR(16) NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT player_to_slug UNIQUE (name, slug),
	FOREIGN KEY(slug) REFERENCES webhook_url (slug)
);

CREATE TABLE player_games (
	slug VARCHAR(16) NOT NULL,
	playerid INTEGER NOT NULL,
	gameid INTEGER NOT NULL,
	PRIMARY KEY (slug, playerid, gameid),
	FOREIGN KEY(slug) REFERENCES webhook_url (slug),
	FOREIGN KEY(playerid) REFERENCES player (id),
	FOREIGN KEY(gameid) REFERENCES game (id)
);

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
);