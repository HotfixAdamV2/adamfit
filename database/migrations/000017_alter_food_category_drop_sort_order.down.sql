/*
    Migration: 000017_alter_food_category_drop_sort_order (down)

    What:
        Re-adds the sort_order column to food_category as it was defined in
        000006 (SMALLINT NOT NULL DEFAULT 0) and restores its values.

    Why:
        Reverts 000017_alter_food_category_drop_sort_order.

    Notes:
        - Values are restored from the 000010 seed list, matched on parent
          name and category name.
        - Any category not in that list gets the next numbers after the
          seeded ones within its parent, in alphabetical order.
*/

ALTER TABLE food_category
    ADD COLUMN sort_order SMALLINT NOT NULL DEFAULT 0;

-- Restore the seeded values (parent_name is NULL for top-level categories)
WITH
    seeded (parent_name, category_name, sort_order) AS (
        VALUES
            (NULL, 'Protein', 1),
            (NULL, 'Grains & starches', 2),
            (NULL, 'Vegetables', 3),
            (NULL, 'Fruit', 4),
            (NULL, 'Dairy', 5),
            (NULL, 'Fats & oils', 6),
            (NULL, 'Seasonings & sauces', 7),
            (NULL, 'Supplements', 8),
            (NULL, 'Snacks & sweets', 9),
            (NULL, 'Soups & prepared meals', 10),
            ('Protein', 'Poultry', 1),
            ('Protein', 'Beef', 2),
            ('Protein', 'Pork', 3),
            ('Protein', 'Deli & breakfast meats', 4),
            ('Protein', 'Fish & seafood', 5),
            ('Protein', 'Eggs', 6),
            ('Protein', 'Plant protein', 7),
            ('Grains & starches', 'Rice', 1),
            ('Grains & starches', 'Pasta', 2),
            ('Grains & starches', 'Bread & tortillas', 3),
            ('Grains & starches', 'Oats & cereal', 4),
            ('Grains & starches', 'Potatoes', 5),
            ('Grains & starches', 'Flours & mixes', 6),
            ('Vegetables', 'Leafy greens', 1),
            ('Vegetables', 'Cruciferous', 2),
            ('Vegetables', 'Other vegetables', 3),
            ('Fruit', 'Berries', 1),
            ('Fruit', 'Other fruit', 2),
            ('Dairy', 'Milk', 1),
            ('Dairy', 'Yogurt', 2),
            ('Dairy', 'Cheese', 3),
            ('Dairy', 'Other dairy', 4),
            ('Fats & oils', 'Oils & butter', 1),
            ('Fats & oils', 'Nuts & seeds', 2),
            ('Fats & oils', 'Other fats', 3),
            ('Seasonings & sauces', 'Spices & mixes', 1),
            ('Seasonings & sauces', 'Sauces & condiments', 2),
            ('Supplements', 'Protein powders', 1),
            ('Supplements', 'Protein shakes', 2),
            ('Supplements', 'Protein bars', 3),
            ('Supplements', 'Other supplements', 4),
            ('Snacks & sweets', 'Chips & crackers', 1),
            ('Snacks & sweets', 'Snack bars', 2),
            ('Snacks & sweets', 'Sweets & desserts', 3),
            ('Soups & prepared meals', 'Soups', 1),
            ('Soups & prepared meals', 'Prepared meals', 2)
    )
UPDATE food_category AS fc
SET sort_order = s.sort_order
FROM seeded AS s
LEFT JOIN food_category AS parent
    ON parent.category_name = s.parent_name
    AND parent.parent_category_id IS NULL
WHERE fc.category_name = s.category_name
    AND fc.parent_category_id IS NOT DISTINCT FROM parent.category_id;

-- Number any categories added after the seed, alphabetically after the seeded ones
WITH
    unseeded AS (
        SELECT
            fc.category_id,
            row_number() OVER (
                PARTITION BY fc.parent_category_id
                ORDER BY fc.category_name
            ) AS position
        FROM food_category AS fc
        WHERE fc.sort_order = 0
    ),
    seeded_max AS (
        SELECT
            parent_category_id,
            MAX(sort_order) AS max_sort_order
        FROM food_category
        GROUP BY parent_category_id
    )
UPDATE food_category AS fc
SET sort_order = sm.max_sort_order + u.position
FROM unseeded AS u
INNER JOIN food_category AS src
    ON src.category_id = u.category_id
INNER JOIN seeded_max AS sm
    ON sm.parent_category_id IS NOT DISTINCT FROM src.parent_category_id
WHERE fc.category_id = u.category_id;
