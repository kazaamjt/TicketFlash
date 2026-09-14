CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE user-metadata (
    id UUID PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    address TEXT,
    postal_code INTEGER,
    city TEXT,
    telephone TEXT
);
