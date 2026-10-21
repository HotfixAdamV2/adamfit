/*
    Migration: 000020_create_fx_trg_food_validate_category (down)

    What:
        Drops the category-ownership triggers on food and standard_food and
        their trigger functions.

    Why:
        Reverts 000020_create_fx_trg_food_validate_category.
*/

DROP TRIGGER trg_standard_food_validate_category ON standard_food;

DROP TRIGGER trg_food_validate_category ON food;

DROP FUNCTION fx_trg_standard_food_validate_category();

DROP FUNCTION fx_trg_food_validate_category();
