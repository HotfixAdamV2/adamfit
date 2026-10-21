/*
    Migration: 000010_seed_standard_food (down)

    What:
        Removes the seeded standard foods and food categories.

    Why:
        Reverts 000010_seed_standard_food.
*/

DELETE FROM standard_food;

-- Sub-categories first, because they reference their parents
DELETE FROM food_category
WHERE parent_category_id IS NOT NULL;

DELETE FROM food_category;
