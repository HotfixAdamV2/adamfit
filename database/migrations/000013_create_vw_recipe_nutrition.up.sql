/*
    Migration: 000013_create_vw_recipe_nutrition (up)

    What:
        Creates the vw_recipe_nutrition view: one row per recipe with its
        total macros and its macros per serving.

    Why:
        Recipe macros are always calculated from the ingredients, never
        stored, so they can't drift out of date. Doing the maths in one
        view keeps the recipe page and the daily log consistent.

    Notes:
        - Recipes with no ingredients yet still appear, with zeros.
        - Per-serving values are the totals divided by servings_per_recipe.
*/

CREATE VIEW vw_recipe_nutrition AS
WITH
    recipe_total AS (
        SELECT
            r.recipe_id,
            COALESCE(SUM(ri.servings * f.calories), 0) AS total_calories,
            COALESCE(SUM(ri.servings * f.protein_g), 0) AS total_protein_g,
            COALESCE(SUM(ri.servings * f.carbs_g), 0) AS total_carbs_g,
            COALESCE(SUM(ri.servings * f.fat_g), 0) AS total_fat_g,
            COALESCE(SUM(ri.servings * f.fiber_g), 0) AS total_fiber_g
        FROM recipe AS r
        LEFT JOIN recipe_ingredient AS ri
            ON ri.recipe_id = r.recipe_id
        LEFT JOIN food AS f
            ON f.food_id = ri.food_id
        GROUP BY r.recipe_id
    )
SELECT
    r.recipe_id,
    r.user_id,
    r.recipe_name,
    r.servings_per_recipe,
    r.serving_label,
    r.is_active,
    ROUND(rt.total_calories, 2) AS total_calories,
    ROUND(rt.total_protein_g, 2) AS total_protein_g,
    ROUND(rt.total_carbs_g, 2) AS total_carbs_g,
    ROUND(rt.total_fat_g, 2) AS total_fat_g,
    ROUND(rt.total_fiber_g, 2) AS total_fiber_g,
    ROUND(rt.total_calories / r.servings_per_recipe, 2) AS calories,
    ROUND(rt.total_protein_g / r.servings_per_recipe, 2) AS protein_g,
    ROUND(rt.total_carbs_g / r.servings_per_recipe, 2) AS carbs_g,
    ROUND(rt.total_fat_g / r.servings_per_recipe, 2) AS fat_g,
    ROUND(rt.total_fiber_g / r.servings_per_recipe, 2) AS fiber_g
FROM recipe AS r
INNER JOIN recipe_total AS rt
    ON rt.recipe_id = r.recipe_id;
