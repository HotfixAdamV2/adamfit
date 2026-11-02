/*
    Migration: 000035_create_exercise_muscle_group (down)

    What:
        Drops trg_exercise_validate and its function, then the
        exercise_muscle_group table (with its index and trigger) and the
        fx_trg_exercise_muscle_group_validate function.

    Why:
        Reverts 000035_create_exercise_muscle_group.

    Notes:
        - Data loss: every exercise's muscle tags are deleted.
*/

DROP TRIGGER trg_exercise_validate ON exercise;

DROP FUNCTION fx_trg_exercise_validate();

DROP TABLE exercise_muscle_group;

DROP FUNCTION fx_trg_exercise_muscle_group_validate();
