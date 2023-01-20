
CREATE TABLE player (
	id SERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	slug VARCHAR(16) NOT NULL, 
	discordid BIGINT, 
	PRIMARY KEY (id), 
	CONSTRAINT player_to_slug UNIQUE (name, slug), 
	FOREIGN KEY(slug) REFERENCES webhook_url (slug)
)

