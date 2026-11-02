/*
    Migration: 000036_create_fx_trg_muscle_group_validate (down)

    What:
        Drops the trg_muscle_group_validate trigger and the
        fx_trg_muscle_group_validate function.

    Why:
        Reverts 000036_create_fx_trg_muscle_group_validate.
*/

DROP TRIGGER trg_muscle_group_validate ON muscle_group;

DROP FUNCTION fx_trg_muscle_group_validate();
