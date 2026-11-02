/*
    Migration: 000038_create_fx_trg_copy_standard_exercises (up)

    What:
        Creates the trigger function fx_trg_copy_standard_exercises and
        attaches it to app_user (AFTER INSERT), so every new user gets a
        copy of standard_exercise in their own exercise list, with the
        muscle tags copied into exercise_muscle_group. Also copies the
        list to every existing user.

    Why:
        Each user owns an editable copy of the standard exercises, the
        same way 000012 does for foods. Doing the copy in the database
        means it happens no matter how the user is created.

    Notes:
        - Tags are mapped to the new rows through standard_exercise_id,
          which is unique per user straight after the copy.
        - Standard tags only use built-in muscle groups (000032), so every
          copied tag passes fx_trg_exercise_muscle_group_validate.
        - The backfill assumes no existing user has exercises yet, which
          is true because the table was created in 000034.
*/

-- Trigger function
CREATE FUNCTION fx_trg_copy_standard_exercises()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO exercise (
        user_id,
        exercise_name,
        exercise_type,
        equipment,
        instructions,
        standard_exercise_id
    )
    SELECT
        NEW.user_id,
        exercise_name,
        exercise_type,
        equipment,
        instructions,
        standard_exercise_id
    FROM standard_exercise;

    INSERT INTO exercise_muscle_group (
        exercise_id,
        muscle_group_id,
        is_primary
    )
    SELECT
        e.exercise_id,
        semg.muscle_group_id,
        semg.is_primary
    FROM standard_exercise_muscle_group AS semg
    INNER JOIN exercise AS e
        ON e.standard_exercise_id = semg.standard_exercise_id
        AND e.user_id = NEW.user_id;

    RETURN NEW;
END;
$$;

-- Trigger assignments
CREATE TRIGGER trg_app_user_copy_standard_exercises
    AFTER INSERT ON app_user
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_copy_standard_exercises();

-- Backfill users that already exist
INSERT INTO exercise (
    user_id,
    exercise_name,
    exercise_type,
    equipment,
    instructions,
    standard_exercise_id
)
SELECT
    au.user_id,
    se.exercise_name,
    se.exercise_type,
    se.equipment,
    se.instructions,
    se.standard_exercise_id
FROM app_user AS au
CROSS JOIN standard_exercise AS se;

INSERT INTO exercise_muscle_group (
    exercise_id,
    muscle_group_id,
    is_primary
)
SELECT
    e.exercise_id,
    semg.muscle_group_id,
    semg.is_primary
FROM standard_exercise_muscle_group AS semg
INNER JOIN exercise AS e
    ON e.standard_exercise_id = semg.standard_exercise_id;
