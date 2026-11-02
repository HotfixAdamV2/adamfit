/*
    Migration: 000035_create_exercise_muscle_group (up)

    What:
        Creates the exercise_muscle_group table, which tags each user
        exercise with the muscle groups it works, and two trigger
        functions with their triggers:
        - fx_trg_exercise_muscle_group_validate on exercise_muscle_group:
          the muscle group must be built-in (user_id NULL) or owned by the
          exercise's user.
        - fx_trg_exercise_validate on exercise: an exercise's user_id can
          never change.

    Why:
        Since muscle groups can belong to a user (000029), a foreign key
        only checks that the group exists, not who owns it. Without the
        check, an exercise could be tagged with another user's private
        group. The ownership check is only sound if an exercise cannot be
        moved to another user afterwards, hence the second trigger.

    Notes:
        - The primary key is (exercise_id, muscle_group_id), so a muscle
          is either primary or secondary for an exercise, never both. To
          switch it, UPDATE is_primary.
        - ON DELETE CASCADE on exercise_id removes the tags with the
          exercise (and so with the user). The muscle group foreign key
          has no cascade: a group that is still tagged cannot be hard
          deleted (23503 fk_exercise_muscle_group_muscle_group_id).
        - Errors the app should catch (psycopg: e.sqlstate and
          e.diag.constraint_name):
            * 23503 foreign_key_violation,
              fk_exercise_muscle_group_muscle_group_id: the group belongs
              to another user (or does not exist).
            * 23514 check_violation, chk_exercise_user_id: an attempt to
              change exercise.user_id.
        - Tagging an inactive muscle group is not blocked, in the same
          way 000020 lets a food point at an inactive category. The app
          should offer only active groups in its pickers.
        - Muscle tags only make sense for strength exercises, but this is
          not enforced here: an exercise's type can be changed after it is
          tagged, so a correct rule would need checks on both tables. The
          app hides or ignores tags on cardio exercises.
*/

-- Create the table
CREATE TABLE exercise_muscle_group (
    -- Fields
    exercise_id INTEGER NOT NULL,
    muscle_group_id INTEGER NOT NULL,
    is_primary BOOLEAN NOT NULL,
    -- Constraints
    CONSTRAINT pk_exercise_muscle_group_exercise_id_muscle_group_id
        PRIMARY KEY (exercise_id, muscle_group_id),
    CONSTRAINT fk_exercise_muscle_group_exercise_id FOREIGN KEY (exercise_id)
        REFERENCES exercise (exercise_id) ON DELETE CASCADE,
    CONSTRAINT fk_exercise_muscle_group_muscle_group_id FOREIGN KEY (muscle_group_id)
        REFERENCES muscle_group (muscle_group_id)
);

-- Create indexes
CREATE INDEX idx_exercise_muscle_group_muscle_group_id
    ON exercise_muscle_group (muscle_group_id);

-- Trigger function for exercise_muscle_group
CREATE FUNCTION fx_trg_exercise_muscle_group_validate()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    exercise_user_id INTEGER;
    group_user_id INTEGER;
BEGIN
    SELECT
        user_id
    INTO group_user_id
    FROM muscle_group
    WHERE muscle_group_id = NEW.muscle_group_id;

    -- A missing group is left to fk_exercise_muscle_group_muscle_group_id
    IF NOT FOUND OR group_user_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT
        user_id
    INTO exercise_user_id
    FROM exercise
    WHERE exercise_id = NEW.exercise_id;

    -- A missing exercise is left to fk_exercise_muscle_group_exercise_id
    IF FOUND AND group_user_id <> exercise_user_id THEN
        RAISE EXCEPTION 'The muscle group belongs to another user.'
            USING ERRCODE = 'foreign_key_violation',
                CONSTRAINT = 'fk_exercise_muscle_group_muscle_group_id';
    END IF;

    RETURN NEW;
END;
$$;

-- Trigger function for exercise
CREATE FUNCTION fx_trg_exercise_validate()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- The owner of an exercise never changes
    IF NEW.user_id IS DISTINCT FROM OLD.user_id THEN
        RAISE EXCEPTION 'The owner of an exercise cannot be changed.'
            USING ERRCODE = 'check_violation',
                CONSTRAINT = 'chk_exercise_user_id';
    END IF;

    RETURN NEW;
END;
$$;

-- Trigger assignments
CREATE TRIGGER trg_exercise_muscle_group_validate
    BEFORE INSERT OR UPDATE OF exercise_id, muscle_group_id ON exercise_muscle_group
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_exercise_muscle_group_validate();

CREATE TRIGGER trg_exercise_validate
    BEFORE UPDATE OF user_id ON exercise
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_exercise_validate();

-- Give grants
-- None needed: the master role owns the table.
