/*
    Migration: 000017_alter_food_serving_unit_fk (up)

    What:
        Replaces the serving_unit CHECK constraints on standard_food and
        food with foreign keys to the serving_unit lookup table.

    Why:
        So a new unit only needs a row in serving_unit (see 000015).

    Notes:
        - ON UPDATE CASCADE means renaming a unit_code updates every food
          that uses it.
*/

ALTER TABLE standard_food
    DROP CONSTRAINT chk_standard_food_serving_unit,
    ADD CONSTRAINT fk_standard_food_serving_unit FOREIGN KEY (serving_unit)
        REFERENCES serving_unit (unit_code) ON UPDATE CASCADE;

ALTER TABLE food
    DROP CONSTRAINT chk_food_serving_unit,
    ADD CONSTRAINT fk_food_serving_unit FOREIGN KEY (serving_unit)
        REFERENCES serving_unit (unit_code) ON UPDATE CASCADE;
