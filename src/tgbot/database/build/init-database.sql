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
