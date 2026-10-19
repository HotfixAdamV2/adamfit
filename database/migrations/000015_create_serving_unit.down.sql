/*
    Migration: 000015_create_serving_unit (down)

    What:
        Drops the serving_unit table.

    Why:
        Reverts 000015_create_serving_unit.
*/

DROP TABLE serving_unit;
