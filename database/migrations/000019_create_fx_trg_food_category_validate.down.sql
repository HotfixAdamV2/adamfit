/*
    Migration: 000019_create_fx_trg_food_category_validate (down)

    What:
        Drops the trg_food_category_validate trigger and the
        fx_trg_food_category_validate function.

    Why:
        Reverts 000019_create_fx_trg_food_category_validate.
*/

DROP TRIGGER trg_food_category_validate ON food_category;

DROP FUNCTION fx_trg_food_category_validate();
