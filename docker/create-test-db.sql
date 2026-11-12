-- The test suite empties its tables before every test, so it gets its own
-- database and never touches local development data.
CREATE DATABASE expenses_test OWNER expenses;
