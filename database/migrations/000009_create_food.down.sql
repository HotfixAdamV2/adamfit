/*
    Migration: 000009_create_food (down)

    What:
        Drops the food table, its sequence, indexes and trigger.

    Why:
        Reverts 000009_create_food.
*/

DROP TABLE food;
