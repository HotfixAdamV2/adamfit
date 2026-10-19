/*
    Migration: 000017_alter_food_serving_unit_fk (down)

    What:
        Puts back the serving_unit CHECK constraints in place of the
        foreign keys.

    Why:
        Reverts 000017_alter_food_serving_unit_fk.

    Notes:
        - This fails if any food uses a unit that was not in the original
          list (e.g. oz). Change or remove those foods first.
*/

ALTER TABLE food
    DROP CONSTRAINT fk_food_serving_unit,
    ADD CONSTRAINT chk_food_serving_unit
        CHECK (serving_unit IN ('g', 'ml', 'cup', 'tbsp', 'tsp', 'piece', 'slice', 'serving'));

ALTER TABLE standard_food
    DROP CONSTRAINT fk_standard_food_serving_unit,
    ADD CONSTRAINT chk_standard_food_serving_unit
        CHECK (serving_unit IN ('g', 'ml', 'cup', 'tbsp', 'tsp', 'piece', 'slice', 'serving'));
