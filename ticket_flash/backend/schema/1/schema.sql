CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE
);
CREATE TABLE user_metadata (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    address VARCHAR(1000),
    postal_code INTEGER,
    city VARCHAR(255),
    telephone VARCHAR(20)
);
