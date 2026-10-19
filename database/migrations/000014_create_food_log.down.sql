/*
    Migration: 000014_create_food_log (down)

    What:
        Drops the food_log table, its sequence, indexes and trigger.

    Why:
        Reverts 000014_create_food_log.
*/

DROP TABLE food_log;
