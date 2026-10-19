/*
    Migration: 000015_create_vw_recipe_nutrition (down)

    What:
        Drops the vw_recipe_nutrition view.

    Why:
        Reverts 000015_create_vw_recipe_nutrition.
*/

DROP VIEW vw_recipe_nutrition;
