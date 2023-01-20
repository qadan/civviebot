
CREATE TABLE webhook_url (
	slug VARCHAR(16) NOT NULL, 
	channelid BIGINT NOT NULL, 
	PRIMARY KEY (slug), 
	UNIQUE (channelid)
)

