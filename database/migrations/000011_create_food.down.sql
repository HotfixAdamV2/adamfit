/*
    Migration: 000011_create_food (down)

    What:
        Drops the food table, its sequence, indexes and trigger.

    Why:
        Reverts 000011_create_food.
*/

DROP TABLE food;
