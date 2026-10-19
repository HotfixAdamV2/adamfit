/*
    Migration: 000009_create_standard_food (down)

    What:
        Drops the standard_food table and its sequence.

    Why:
        Reverts 000009_create_standard_food.
*/

DROP TABLE standard_food;
