/*
    Migration: 000032_create_standard_exercise_muscle_group (down)

    What:
        Drops the standard_exercise_muscle_group table (with its index and
        trigger) and the fx_trg_standard_exercise_muscle_group_validate
        function.

    Why:
        Reverts 000032_create_standard_exercise_muscle_group.
*/

DROP TABLE standard_exercise_muscle_group;

DROP FUNCTION fx_trg_standard_exercise_muscle_group_validate();
