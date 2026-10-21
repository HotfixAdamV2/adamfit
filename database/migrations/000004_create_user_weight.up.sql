/*
    Migration: 000004_create_user_weight (up)

    What:
        Creates the user_weight table: one weigh-in per user per day.

    Why:
        The profile page lets a user record their weight on any date and
        charts it over time with a rolling average. Keeping one row per day
        (enforced by unq_user_weight_user_id_weigh_date) means re-entering a
        date simply corrects that day's value.

    Notes:
        - Weight is always stored in kilograms. The UI converts to pounds.
          Three decimal places keep pound values from drifting when
          converted back and forth (e.g. 180.0 lb -> 81.647 kg -> 180.0 lb).
        - Rows are removed automatically if their user is deleted.
        - The unique constraint's index also covers lookups by user_id, so
          no separate index is needed.
*/

-- Create sequence
CREATE SEQUENCE seq_user_weight_weight_id AS INT
    INCREMENT BY 1
    MINVALUE 1
    START WITH 1
    NO CYCLE;

-- Create the table
CREATE TABLE user_weight (
    -- Fields
    weight_id INTEGER NOT NULL DEFAULT nextval('seq_user_weight_weight_id'),
    user_id INTEGER NOT NULL,
    weigh_date DATE NOT NULL,
    weight_kg NUMERIC(6, 3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    CONSTRAINT pk_user_weight_weight_id PRIMARY KEY (weight_id),
    CONSTRAINT fk_user_weight_user_id FOREIGN KEY (user_id)
        REFERENCES app_user (user_id) ON DELETE CASCADE,
    CONSTRAINT unq_user_weight_user_id_weigh_date UNIQUE (user_id, weigh_date),
    CONSTRAINT chk_user_weight_weight_kg CHECK (weight_kg > 0 AND weight_kg < 700)
);

ALTER SEQUENCE seq_user_weight_weight_id OWNED BY user_weight.weight_id;

-- Give grants
-- None needed: the master role owns the table.
