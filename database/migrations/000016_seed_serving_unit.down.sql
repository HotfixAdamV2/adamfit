/*
    Migration: 000016_seed_serving_unit (down)

    What:
        Removes the seeded serving units.

    Why:
        Reverts 000016_seed_serving_unit.
*/

DELETE FROM serving_unit;
