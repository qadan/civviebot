
CREATE TABLE game (
	id SERIAL NOT NULL, 
	name VARCHAR NOT NULL, 
	slug VARCHAR(16) NOT NULL, 
	muted BOOLEAN NOT NULL, 
	duplicatewarned BOOLEAN, 
	remindinterval INTEGER NOT NULL, 
	nextremind TIMESTAMP WITHOUT TIME ZONE, 
	minturns INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT game_to_slug UNIQUE (name, slug), 
	FOREIGN KEY(slug) REFERENCES webhook_url (slug)
)

