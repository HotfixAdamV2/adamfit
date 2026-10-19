/*
    Migration: 000012_create_fx_trg_copy_standard_foods (down)

    What:
        Drops the copy trigger and function, and removes the foods that
        the up migration and trigger copied from standard_food.

    Why:
        Reverts 000012_create_fx_trg_copy_standard_foods.
*/

DROP TRIGGER trg_app_user_copy_standard_foods ON app_user;

DROP FUNCTION fx_trg_copy_standard_foods();

DELETE FROM food
WHERE standard_food_id IS NOT NULL;
