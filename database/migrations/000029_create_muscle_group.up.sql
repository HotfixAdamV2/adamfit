/*
    Migration: 000029_create_muscle_group (up)

    What:
        Creates the muscle_group table: the muscles an exercise can be
        tagged with (Chest, Lats, Quads, ...), and attaches
        fx_trg_set_updated_at.

    Why:
        Strength exercises are tagged with the muscles they work, so the
        app can filter the exercise list and show which muscles a workout
        hit. A NULL user_id is a built-in group that every user sees. A
        value is that user's own group, which only they see. Like food
        categories, deleting a group in the app sets is_active to FALSE.

    Notes:
        - ON DELETE CASCADE removes a user's groups with the user.
        - unq_muscle_group_user_id_muscle_group_name is a unique index on
          (user_id, LOWER(muscle_group_name)) with NULLS NOT DISTINCT, so:
            * built-in rows (user_id NULL) are unique among themselves;
            * each user's rows are unique among that user's rows;
            * "Chest" and "chest" collide.
          It is NOT partial: it covers inactive rows too, so there is one
          row per (owner, lower(name)) and the app can reactivate a removed
          group with:
              INSERT ... ON CONFLICT (user_id, LOWER(muscle_group_name))
              DO UPDATE SET is_active = TRUE WHERE NOT muscle_group.is_active
          (see 000021 for why ON CONFLICT needs a non-partial index). An
          index is needed because a constraint cannot use an expression.
        - The index leads with user_id, so it also serves "the groups a
          user can see" lookups; no separate idx_muscle_group_user_id.
        - A user group with the same name as a built-in one, owner
          changes, and soft-deleting a group still in use are handled by
          fx_trg_muscle_group_validate (000036), because they compare rows
          with different owners or look at other tables.
*/

-- Create sequence
CREATE SEQUENCE seq_muscle_group_muscle_group_id AS INT
    INCREMENT BY 1
    MINVALUE 1
    START WITH 1
    NO CYCLE;

-- Create the table
CREATE TABLE muscle_group (
    -- Fields
    muscle_group_id INTEGER NOT NULL DEFAULT nextval('seq_muscle_group_muscle_group_id'),
    user_id INTEGER,
    muscle_group_name VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    CONSTRAINT pk_muscle_group_muscle_group_id PRIMARY KEY (muscle_group_id),
    CONSTRAINT fk_muscle_group_user_id FOREIGN KEY (user_id)
        REFERENCES app_user (user_id) ON DELETE CASCADE,
    CONSTRAINT chk_muscle_group_muscle_group_name CHECK (LENGTH(TRIM(muscle_group_name)) > 0)
);

ALTER SEQUENCE seq_muscle_group_muscle_group_id OWNED BY muscle_group.muscle_group_id;

-- Create indexes
CREATE UNIQUE INDEX unq_muscle_group_user_id_muscle_group_name
    ON muscle_group (user_id, LOWER(muscle_group_name))
    NULLS NOT DISTINCT;

-- Trigger assignments
CREATE TRIGGER trg_muscle_group_set_updated_at
    BEFORE UPDATE ON muscle_group
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_set_updated_at();

-- Give grants
-- None needed: the master role owns the table.
