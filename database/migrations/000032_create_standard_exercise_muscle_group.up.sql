/*
    Migration: 000032_create_standard_exercise_muscle_group (up)

    What:
        Creates the standard_exercise_muscle_group table, which tags each
        standard exercise with the muscle groups it works, plus the
        trigger function fx_trg_standard_exercise_muscle_group_validate
        and its trigger.

    Why:
        A standard exercise works several muscles, some as the main
        target (primary) and some as helpers (secondary). These tags are
        copied to each user's exercise_muscle_group (see 000038).

    Notes:
        - The primary key is (standard_exercise_id, muscle_group_id), so
          a muscle is either primary or secondary for an exercise, never
          both. It is named pk_standard_exercise_muscle_group (table name
          only) because pk_ + table + both column names would be 70
          characters, over the 63-character identifier limit.
        - ON DELETE CASCADE on standard_exercise_id removes the tags with
          the exercise. The muscle group foreign key has no cascade: a
          built-in group that is still used cannot be deleted.
        - Standard exercises are shared, so they may only use built-in
          muscle groups (user_id NULL). A foreign key cannot check that,
          so the trigger raises SQLSTATE 23503 (foreign_key_violation)
          with constraint fk_standard_exercise_muscle_group_muscle_group_id.
        - idx_standard_exercise_muscle_group_muscle_group_id speeds up
          "is this group used?" checks (000036) and the foreign key.
*/

-- Create the table
CREATE TABLE standard_exercise_muscle_group (
    -- Fields
    standard_exercise_id INTEGER NOT NULL,
    muscle_group_id INTEGER NOT NULL,
    is_primary BOOLEAN NOT NULL,
    -- Constraints
    CONSTRAINT pk_standard_exercise_muscle_group PRIMARY KEY (standard_exercise_id, muscle_group_id),
    CONSTRAINT fk_standard_exercise_muscle_group_standard_exercise_id FOREIGN KEY (standard_exercise_id)
        REFERENCES standard_exercise (standard_exercise_id) ON DELETE CASCADE,
    CONSTRAINT fk_standard_exercise_muscle_group_muscle_group_id FOREIGN KEY (muscle_group_id)
        REFERENCES muscle_group (muscle_group_id)
);

-- Create indexes
CREATE INDEX idx_standard_exercise_muscle_group_muscle_group_id
    ON standard_exercise_muscle_group (muscle_group_id);

-- Trigger function
CREATE FUNCTION fx_trg_standard_exercise_muscle_group_validate()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    group_user_id INTEGER;
BEGIN
    SELECT
        user_id
    INTO group_user_id
    FROM muscle_group
    WHERE muscle_group_id = NEW.muscle_group_id;

    -- A missing group is left to fk_standard_exercise_muscle_group_muscle_group_id
    IF FOUND AND group_user_id IS NOT NULL THEN
        RAISE EXCEPTION 'Standard exercises can only use built-in (shared) muscle groups.'
            USING ERRCODE = 'foreign_key_violation',
                CONSTRAINT = 'fk_standard_exercise_muscle_group_muscle_group_id';
    END IF;

    RETURN NEW;
END;
$$;

-- Trigger assignments
CREATE TRIGGER trg_standard_exercise_muscle_group_validate
    BEFORE INSERT OR UPDATE OF muscle_group_id ON standard_exercise_muscle_group
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_standard_exercise_muscle_group_validate();

-- Give grants
-- None needed: the master role owns the table.
