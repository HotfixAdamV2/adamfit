/*
    Migration: 000012_create_recipe_ingredient (down)

    What:
        Drops the recipe_ingredient table, its sequence, indexes and trigger.

    Why:
        Reverts 000012_create_recipe_ingredient.
*/

DROP TABLE recipe_ingredient;
