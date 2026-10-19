/*
    Migration: 000011_create_recipe (down)

    What:
        Drops the recipe table, its sequence, indexes and trigger.

    Why:
        Reverts 000011_create_recipe.
*/

DROP TABLE recipe;
