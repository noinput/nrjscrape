BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "songs" (
	"musicId"	TEXT UNIQUE,
	"artist"	TEXT,
	"title"	TEXT,
	"startTime"	TEXT,
	PRIMARY KEY("musicId")
);
COMMIT;
