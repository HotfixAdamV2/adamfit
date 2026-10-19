/*
    Migration: 000008_seed_standard_food (up)

    What:
        Inserts the food categories, their sub-categories, and the starter
        list of standard foods.

    Why:
        Users should not have to type in common foods before they can
        start tracking. Values are approximate, based on USDA FoodData
        Central, and each user can edit their own copy.

    Notes:
        - Category ids are looked up by name rather than hard-coded.
        - Meats, grains and vegetables use a 100 g raw/dry serving so
          users can scale by weight. Items normally counted or measured
          (eggs, oil, sauces) use their usual household serving.
*/

-- Top-level categories
INSERT INTO food_category (
    category_name,
    sort_order
)
VALUES
    ('Protein', 1),
    ('Grains & starches', 2),
    ('Vegetables', 3),
    ('Fruit', 4),
    ('Dairy', 5),
    ('Fats & oils', 6),
    ('Seasonings & sauces', 7);

-- Sub-categories
WITH
    sub_category (parent_name, category_name, sort_order) AS (
        VALUES
            ('Protein', 'Poultry', 1),
            ('Protein', 'Beef', 2),
            ('Protein', 'Pork', 3),
            ('Protein', 'Fish & seafood', 4),
            ('Protein', 'Eggs', 5),
            ('Protein', 'Plant protein', 6),
            ('Grains & starches', 'Rice', 1),
            ('Grains & starches', 'Pasta', 2),
            ('Grains & starches', 'Bread & tortillas', 3),
            ('Grains & starches', 'Oats & cereal', 4),
            ('Grains & starches', 'Potatoes', 5),
            ('Vegetables', 'Leafy greens', 1),
            ('Vegetables', 'Cruciferous', 2),
            ('Vegetables', 'Other vegetables', 3),
            ('Fruit', 'Berries', 1),
            ('Fruit', 'Other fruit', 2),
            ('Dairy', 'Milk', 1),
            ('Dairy', 'Yogurt', 2),
            ('Dairy', 'Cheese', 3),
            ('Fats & oils', 'Oils & butter', 1),
            ('Fats & oils', 'Nuts & seeds', 2),
            ('Fats & oils', 'Other fats', 3),
            ('Seasonings & sauces', 'Spices & mixes', 1),
            ('Seasonings & sauces', 'Sauces & condiments', 2)
    )
INSERT INTO food_category (
    category_name,
    parent_category_id,
    sort_order
)
SELECT
    sc.category_name,
    parent.category_id,
    sc.sort_order
FROM sub_category AS sc
INNER JOIN food_category AS parent
    ON parent.category_name = sc.parent_name
    AND parent.parent_category_id IS NULL;

-- Standard foods (macros are per serving)
WITH
    seed (sub_category, food_name, serving_size, serving_unit, calories, protein_g, carbs_g, fat_g, fiber_g) AS (
        VALUES
            ('Poultry', 'Chicken breast, boneless skinless (raw)', 100, 'g', 120, 22.5, 0, 2.6, 0),
            ('Poultry', 'Chicken thigh, boneless skinless (raw)', 100, 'g', 120, 19.7, 0, 3.9, 0),
            ('Poultry', 'Ground turkey, 93% lean (raw)', 100, 'g', 150, 18.7, 0, 8.3, 0),
            ('Beef', 'Ground beef, 80% lean (raw)', 100, 'g', 254, 17.2, 0, 20, 0),
            ('Beef', 'Ground beef, 93% lean (raw)', 100, 'g', 152, 20.9, 0, 7, 0),
            ('Beef', 'Ground beef, 96% lean (raw)', 100, 'g', 125, 21.5, 0, 4, 0),
            ('Beef', 'Sirloin steak, trimmed (raw)', 100, 'g', 143, 21.6, 0, 5.7, 0),
            ('Pork', 'Pork tenderloin (raw)', 100, 'g', 109, 21, 0, 2.2, 0),
            ('Fish & seafood', 'Salmon, Atlantic (raw)', 100, 'g', 208, 20.4, 0, 13.4, 0),
            ('Fish & seafood', 'Shrimp (raw)', 100, 'g', 85, 20.1, 0, 0.5, 0),
            ('Fish & seafood', 'Cod (raw)', 100, 'g', 82, 17.8, 0, 0.7, 0),
            ('Fish & seafood', 'Tuna, canned in water (drained)', 100, 'g', 116, 25.5, 0, 0.8, 0),
            ('Eggs', 'Egg, large (whole)', 1, 'piece', 72, 6.3, 0.4, 4.8, 0),
            ('Eggs', 'Egg whites (liquid)', 100, 'g', 52, 10.9, 0.7, 0.2, 0),
            ('Plant protein', 'Tofu, firm', 100, 'g', 144, 17.3, 2.8, 8.7, 2.3),
            ('Plant protein', 'Black beans, canned (drained)', 100, 'g', 91, 6, 16.6, 0.3, 6.9),
            ('Rice', 'White rice, long grain (dry)', 100, 'g', 365, 7.1, 80, 0.7, 1.3),
            ('Rice', 'Brown rice (dry)', 100, 'g', 370, 7.9, 77.2, 2.9, 3.5),
            ('Rice', 'Jasmine rice (dry)', 100, 'g', 356, 6.7, 78.9, 0.6, 1.1),
            ('Pasta', 'Pasta, enriched (dry)', 100, 'g', 371, 13, 75, 1.5, 3.2),
            ('Bread & tortillas', 'Whole wheat bread', 1, 'slice', 80, 4, 14, 1, 2),
            ('Bread & tortillas', 'Flour tortilla, 8 inch', 1, 'piece', 146, 3.9, 24, 3.6, 1.7),
            ('Oats & cereal', 'Rolled oats (dry)', 100, 'g', 379, 13.2, 67.7, 6.5, 10.1),
            ('Potatoes', 'Russet potato (raw)', 100, 'g', 79, 2.1, 18, 0.1, 1.3),
            ('Potatoes', 'Sweet potato (raw)', 100, 'g', 86, 1.6, 20.1, 0.1, 3),
            ('Leafy greens', 'Spinach (raw)', 100, 'g', 23, 2.9, 3.6, 0.4, 2.2),
            ('Leafy greens', 'Romaine lettuce (raw)', 100, 'g', 17, 1.2, 3.3, 0.3, 2.1),
            ('Cruciferous', 'Broccoli (raw)', 100, 'g', 34, 2.8, 6.6, 0.4, 2.6),
            ('Cruciferous', 'Cauliflower (raw)', 100, 'g', 25, 1.9, 5, 0.3, 2),
            ('Other vegetables', 'Green beans (raw)', 100, 'g', 31, 1.8, 7, 0.2, 2.7),
            ('Other vegetables', 'Red bell pepper (raw)', 100, 'g', 31, 1, 6, 0.3, 2.1),
            ('Other vegetables', 'Yellow onion (raw)', 100, 'g', 40, 1.1, 9.3, 0.1, 1.7),
            ('Other vegetables', 'Asparagus (raw)', 100, 'g', 20, 2.2, 3.9, 0.1, 2.1),
            ('Berries', 'Blueberries', 100, 'g', 57, 0.7, 14.5, 0.3, 2.4),
            ('Berries', 'Strawberries', 100, 'g', 32, 0.7, 7.7, 0.3, 2),
            ('Other fruit', 'Banana, medium', 1, 'piece', 105, 1.3, 27, 0.4, 3.1),
            ('Other fruit', 'Apple, medium', 1, 'piece', 95, 0.5, 25, 0.3, 4.4),
            ('Other fruit', 'Avocado', 100, 'g', 160, 2, 8.5, 14.7, 6.7),
            ('Milk', 'Milk, 2%', 1, 'cup', 122, 8.1, 11.7, 4.8, 0),
            ('Yogurt', 'Greek yogurt, plain nonfat', 100, 'g', 59, 10.2, 3.6, 0.4, 0),
            ('Yogurt', 'Cottage cheese, 2%', 100, 'g', 84, 11, 4.3, 2.3, 0),
            ('Cheese', 'Cheddar cheese', 28, 'g', 114, 7, 0.4, 9.4, 0),
            ('Cheese', 'Mozzarella, part skim', 28, 'g', 72, 6.9, 0.8, 4.5, 0),
            ('Oils & butter', 'Olive oil', 1, 'tbsp', 119, 0, 0, 13.5, 0),
            ('Oils & butter', 'Butter', 1, 'tbsp', 102, 0.1, 0, 11.5, 0),
            ('Nuts & seeds', 'Almonds', 28, 'g', 164, 6, 6.1, 14.2, 3.5),
            ('Nuts & seeds', 'Peanut butter, smooth', 2, 'tbsp', 191, 7.1, 7.1, 16.4, 1.6),
            ('Spices & mixes', 'Taco seasoning', 2, 'tsp', 15, 0.3, 3, 0.2, 0.5),
            ('Spices & mixes', 'Garlic powder', 1, 'tsp', 10, 0.5, 2.3, 0, 0.3),
            ('Spices & mixes', 'Salt', 1, 'tsp', 0, 0, 0, 0, 0),
            ('Sauces & condiments', 'Salsa', 2, 'tbsp', 10, 0.5, 2, 0, 0.5),
            ('Sauces & condiments', 'Soy sauce', 1, 'tbsp', 9, 1.3, 0.8, 0.1, 0.1),
            ('Sauces & condiments', 'Ketchup', 1, 'tbsp', 20, 0.2, 5, 0, 0),
            ('Sauces & condiments', 'BBQ sauce', 2, 'tbsp', 60, 0.3, 14, 0.2, 0.3)
    )
INSERT INTO standard_food (
    food_name,
    category_id,
    serving_size,
    serving_unit,
    calories,
    protein_g,
    carbs_g,
    fat_g,
    fiber_g
)
SELECT
    s.food_name,
    fc.category_id,
    s.serving_size,
    s.serving_unit,
    s.calories,
    s.protein_g,
    s.carbs_g,
    s.fat_g,
    s.fiber_g
FROM seed AS s
INNER JOIN food_category AS fc
    ON fc.category_name = s.sub_category
    AND fc.parent_category_id IS NOT NULL;
