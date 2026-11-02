/*
    Migration: 000036_create_fx_trg_muscle_group_validate (up)

    What:
        Creates the trigger function fx_trg_muscle_group_validate and
        attaches it to muscle_group (BEFORE INSERT OR UPDATE). It enforces
        the rules for user-created muscle groups that a constraint or
        index cannot express.

    Why:
        unq_muscle_group_user_id_muscle_group_name (000029) stops
        duplicates within one owner, but these rules compare rows with
        different owners, or look at other tables, so they need a
        trigger. It comes after 000035 because it reads the tag tables.

    Notes:
        Every error sets a SQLSTATE and a constraint name, so the app can
        catch it (psycopg: e.sqlstate and e.diag.constraint_name):
        - 23514 check_violation, chk_muscle_group_user_id:
          user_id can never change (built-in <-> user, or user A -> B).
        - 23505 unique_violation,
          unq_muscle_group_user_id_muscle_group_name:
          an active user group cannot have the same name (any case) as an
          active built-in group. Checked on insert, rename and
          reactivation. This is the same name the unique index uses for a
          duplicate of the user's own group, so the app can handle both
          the same way.
        - 2BP01 dependent_objects_still_exist, chk_muscle_group_is_active:
          decision: soft-deleting a group (is_active -> FALSE) is BLOCKED
          while any active exercise is tagged with it, or (for built-in
          groups) while any standard exercise is tagged with it. The user
          must untag those exercises first. Tags on inactive exercises do
          not block it.
        Built-in groups are managed by hand, so a new built-in group that
        matches an existing user group is not blocked. Inactive built-in
        groups are ignored by the duplicate check, so a user may make
        their own group with a retired built-in name.
*/

-- Trigger function
CREATE FUNCTION fx_trg_muscle_group_validate()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- The owner of a muscle group never changes
    IF TG_OP = 'UPDATE' AND NEW.user_id IS DISTINCT FROM OLD.user_id THEN
        RAISE EXCEPTION 'The owner of a muscle group cannot be changed.'
            USING ERRCODE = 'check_violation',
                CONSTRAINT = 'chk_muscle_group_user_id';
    END IF;

    -- A user group cannot duplicate an active built-in one
    IF NEW.user_id IS NOT NULL
        AND NEW.is_active
        AND (
            TG_OP = 'INSERT'
            OR LOWER(NEW.muscle_group_name) IS DISTINCT FROM LOWER(OLD.muscle_group_name)
            OR NOT OLD.is_active
        )
        AND EXISTS (
            SELECT
                1
            FROM muscle_group
            WHERE user_id IS NULL
                AND is_active
                AND LOWER(muscle_group_name) = LOWER(NEW.muscle_group_name)
        )
    THEN
        RAISE EXCEPTION 'A built-in muscle group named "%" already exists.', NEW.muscle_group_name
            USING ERRCODE = 'unique_violation',
                CONSTRAINT = 'unq_muscle_group_user_id_muscle_group_name';
    END IF;

    -- Block soft-deleting a group that is still in use
    IF TG_OP = 'UPDATE' AND OLD.is_active AND NOT NEW.is_active THEN
        IF EXISTS (
            SELECT
                1
            FROM exercise_muscle_group AS emg
            INNER JOIN exercise AS e
                ON e.exercise_id = emg.exercise_id
            WHERE emg.muscle_group_id = NEW.muscle_group_id
                AND e.is_active
        ) THEN
            RAISE EXCEPTION 'The muscle group "%" is still used by active exercises. Untag them first.', NEW.muscle_group_name
                USING ERRCODE = 'dependent_objects_still_exist',
                    CONSTRAINT = 'chk_muscle_group_is_active';
        END IF;

        IF EXISTS (
            SELECT
                1
            FROM standard_exercise_muscle_group
            WHERE muscle_group_id = NEW.muscle_group_id
        ) THEN
            RAISE EXCEPTION 'The muscle group "%" is used by standard exercises.', NEW.muscle_group_name
                USING ERRCODE = 'dependent_objects_still_exist',
                    CONSTRAINT = 'chk_muscle_group_is_active';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

-- Trigger assignments
CREATE TRIGGER trg_muscle_group_validate
    BEFORE INSERT OR UPDATE ON muscle_group
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_muscle_group_validate();
