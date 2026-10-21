/*
    Migration: 000003_create_app_user (up)

    What:
        Creates the app_user table, which holds one row per person who can
        log in, along with their basic body details and display preferences.

    Why:
        Phase one needs a login page and a profile page. Even though there is
        only one user today, every user-owned table (starting with
        user_weight) will reference app_user so the app can grow to multiple
        users without reworking the schema.

    Notes:
        - The table is named app_user because USER is a reserved word.
        - Passwords are never stored. password_hash holds an Argon2 hash
          produced by the application.
        - Height is stored in centimetres. The UI converts to feet/inches.
        - unit_system remembers whether the user prefers imperial (lb, ft/in)
          or metric (kg, cm).
*/

-- Create sequence
CREATE SEQUENCE seq_app_user_user_id AS INT
    INCREMENT BY 1
    MINVALUE 1
    START WITH 1
    NO CYCLE;

-- Create the table
CREATE TABLE app_user (
    -- Fields
    user_id INTEGER NOT NULL DEFAULT nextval('seq_app_user_user_id'),
    username VARCHAR(50) NOT NULL,
    password_hash TEXT NOT NULL,
    sex VARCHAR(10),
    height_cm NUMERIC(4, 1),
    birth_date DATE,
    unit_system VARCHAR(8) NOT NULL DEFAULT 'imperial',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    CONSTRAINT pk_app_user_user_id PRIMARY KEY (user_id),
    CONSTRAINT unq_app_user_username UNIQUE (username),
    CONSTRAINT chk_app_user_username CHECK (username = LOWER(username) AND LENGTH(username) >= 3),
    CONSTRAINT chk_app_user_sex CHECK (sex IN ('male', 'female')),
    CONSTRAINT chk_app_user_height_cm CHECK (height_cm > 0 AND height_cm < 300),
    CONSTRAINT chk_app_user_birth_date CHECK (birth_date > DATE '1900-01-01'),
    CONSTRAINT chk_app_user_unit_system CHECK (unit_system IN ('imperial', 'metric'))
);

ALTER SEQUENCE seq_app_user_user_id OWNED BY app_user.user_id;

-- Give grants
-- None needed: the master role owns the table.
