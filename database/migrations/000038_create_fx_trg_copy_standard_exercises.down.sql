/*
    Migration: 000038_create_fx_trg_copy_standard_exercises (down)

    What:
        Drops the copy trigger and function, and removes the exercises
        that the up migration and trigger copied from standard_exercise
        (their muscle tags and images go with them through ON DELETE
        CASCADE).

    Why:
        Reverts 000038_create_fx_trg_copy_standard_exercises.

    Notes:
        - Data loss: copied exercises are deleted even if the user edited
          them, the same as 000012's down. Exercises the user created
          (standard_exercise_id NULL) are kept.
*/

DROP TRIGGER trg_app_user_copy_standard_exercises ON app_user;

DROP FUNCTION fx_trg_copy_standard_exercises();

DELETE FROM exercise
WHERE standard_exercise_id IS NOT NULL;
