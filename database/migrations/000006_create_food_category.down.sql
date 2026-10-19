/*
    Migration: 000006_create_food_category (down)

    What:
        Drops the food_category table and its sequence.

    Why:
        Reverts 000006_create_food_category.
*/

DROP TABLE food_category;
