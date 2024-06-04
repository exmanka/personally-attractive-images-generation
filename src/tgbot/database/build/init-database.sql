CREATE TYPE sexEnum AS ENUM ('male', 'female', 'other');
CREATE TABLE users (
	id SERIAL PRIMARY KEY,
	name VARCHAR(64) NOT NULL,
	surname VARCHAR(64),
	username VARCHAR(32) UNIQUE,
	telegram_id BIGINT UNIQUE NOT NULL,
	sex sexEnum NOT NULL,
	register_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX users_idx
ON users(telegram_id);


CREATE TABLE models (
	id SMALLSERIAL PRIMARY KEY,
	name VARCHAR(32) UNIQUE NOT NULL
);
INSERT INTO models(name) VALUES('dcgan');
INSERT INTO models(name) VALUES('stylegan3');


CREATE TABLE generated_images (
	id SERIAL PRIMARY KEY,
	user_id INT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	model_id SMALLINT UNIQUE NOT NULL REFERENCES models(id) ON DELETE CASCADE,
	rating SMALLINT NOT NULL,
	image BYTEA NOT NULL,
	seed BYTEA NOT NULL,
	generation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

	constraint valid_rating
		check (rating <= 10)
);