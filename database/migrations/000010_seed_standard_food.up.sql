/*
    Migration: 000010_seed_standard_food (up)

    What:
        Inserts the food categories, their sub-categories, and the starter
        list of 91 standard foods.

    Why:
        Users should not have to type in common foods before they can
        start tracking. Each user gets an editable copy of this list
        (see 000012).

    Notes:
        - The foods, serving sizes and macros come from the user's own
          list, data/food_list.csv. golang-migrate cannot read a CSV, so
          the VALUES below were generated once from that file with a
          one-off Python script. Names and numbers are kept exactly as
          written in the CSV (a blank fiber value became 0).
        - CSV serving units were mapped onto serving_unit codes (grams ->
          g, ounces -> oz, slices -> slice, balls -> ball, donuts ->
          donut, second spray -> spray). See 000008.
        - The CSV has no categories, so each food was given the best
          fitting sub-category.
        - Category ids are looked up by name rather than hard-coded. Some
          sub-categories (e.g. Pork, Pasta) have no standard foods yet;
          they are kept for foods users add themselves.
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
    ('Seasonings & sauces', 7),
    ('Supplements', 8),
    ('Snacks & sweets', 9),
    ('Soups & prepared meals', 10);

-- Sub-categories
WITH
    sub_category (parent_name, category_name, sort_order) AS (
        VALUES
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

-- Standard foods (macros are per serving), in the CSV's order
WITH
    seed (sub_category, food_name, serving_size, serving_unit, calories, protein_g, carbs_g, fat_g, fiber_g) AS (
        VALUES
            ('Potatoes', 'Potato (raw)', 150, 'g', 110, 3, 26, 0, 2),
            ('Potatoes', 'Sweet Potato (raw)', 130, 'g', 100, 2, 23, 0, 4),
            ('Beef', 'Steak Sirloin (raw)', 4, 'oz', 175, 25, 0, 8, 0),
            ('Beef', 'Steak Filet (raw)', 4, 'oz', 175, 25, 0, 8, 0),
            ('Beef', 'Steak NY Strip (raw)', 4, 'oz', 260, 22, 0, 19, 0),
            ('Beef', 'Steak Ribeye (raw)', 4, 'oz', 280, 21, 0, 22, 0),
            ('Beef', 'Ground Beef 96% Lean (raw)', 4, 'oz', 140, 24, 0, 4.5, 0),
            ('Beef', 'Ground Beef 93% Lean (raw)', 4, 'oz', 170, 23, 0, 8, 0),
            ('Poultry', 'Ground Turkey 93% Lean (raw)', 4, 'oz', 160, 22, 0, 8, 0),
            ('Poultry', 'Realgood Foods Lightly Breaded Chicken', 4, 'oz', 180, 23, 5, 7, 1),
            ('Poultry', 'Chicken Breast (Raw)', 4, 'oz', 120, 25, 0, 1.5, 0),
            ('Poultry', 'Chicken Thighs (Raw)', 4, 'oz', 180, 25, 0, 8.5, 0),
            ('Eggs', 'Egg Whites', 46, 'ml', 25, 5, 1, 0, 0),
            ('Eggs', 'Eggs', 1, 'egg', 75, 7, 0, 5, 0),
            ('Cheese', 'Cheddar Cheese Fat Free', 28, 'g', 45, 9, 2, 0, 0),
            ('Cheese', 'Cottage Cheese Fat Free', 113, 'g', 80, 12, 6, 0, 0),
            ('Poultry', 'Grilled Chicken Breast (Frozen)', 3, 'oz', 90, 17, 0, 2, 0),
            ('Cheese', 'American Cheese 2% Milk', 1, 'slice', 50, 3, 2, 3.5, 0),
            ('Bread & tortillas', 'White Bread - Light', 1, 'slice', 45, 2.5, 8, 0.5, 1.5),
            ('Fish & seafood', 'Black Tiger Shrimp (Raw)', 4, 'oz', 80, 19, 0, 0.5, 0),
            ('Fish & seafood', 'Cod (Raw)', 4, 'oz', 80, 17, 0, 1, 0),
            ('Fish & seafood', 'Mahi Mahi (Raw)', 3, 'oz', 92, 20, 0, 1.5, 0),
            ('Milk', 'Almond Milk Unsweetened Vanilla', 8, 'oz', 30, 1, 1, 2.5, 1),
            ('Yogurt', 'Greek Yogurt - Oikos Single Serve', 1, 'container', 90, 15, 7, 0, 0),
            ('Yogurt', 'Greek Yogurt Fat Free Plain', 170, 'g', 100, 17, 9, 0, 0),
            ('Cruciferous', 'Cauliflower Rice', 76, 'g', 15, 1, 3, 0, 2),
            ('Bread & tortillas', 'Tortilla, High Fiber Large', 1, 'tortilla', 60, 4, 13, 1.5, 12),
            ('Bread & tortillas', 'Tortilla, High Fiber Small', 3, 'tortilla', 110, 7, 19, 5, 19),
            ('Deli & breakfast meats', 'Black Forest Ham', 2, 'slice', 60, 10, 2, 1.5, 0),
            ('Deli & breakfast meats', 'Honey Ham', 2, 'slice', 70, 11, 5, 1.5, 0),
            ('Bread & tortillas', 'Pita Bread, Joseph', 1, 'pita', 70, 6, 12, 2, 6),
            ('Flours & mixes', 'Kodiak Pancake Mix', 63, 'g', 220, 15, 37, 2.5, 5),
            ('Cheese', 'Cheese Fiesta Blend', 28, 'g', 90, 7, 2, 6, 0),
            ('Berries', 'Blackberries', 144, 'g', 60, 2, 14, 0, 8),
            ('Berries', 'Blueberries', 140, 'g', 70, 1, 17, 1, 4),
            ('Other fruit', 'Strawberry & Banana Frozen Mix', 140, 'g', 80, 0, 20, 0, 3),
            ('Cruciferous', 'Broccoli (Raw)', 148, 'g', 50, 4.2, 10, 0.5, 3.8),
            ('Sweets & desserts', 'Gummy Bears, Haribo', 30, 'g', 100, 2, 23, 0, 0),
            ('Soups', 'Progresso Chicken Noodle Soup', 1, 'can', 130, 11, 19, 1.5, 2),
            ('Soups', 'Progresso Santa Fe Chicken Soup', 1, 'can', 160, 11, 29, 2.5, 8),
            ('Soups', 'Progresso Chicken Pot Pie Soup', 1, 'can', 190, 9, 31, 4, 2),
            ('Soups', 'Progresso Beef Pot Roast', 1, 'can', 150, 11, 20, 2.5, 3),
            ('Soups', 'Progresso Chicken & Dumpling', 1, 'can', 160, 11, 23, 2.5, 3),
            ('Sweets & desserts', 'Pudding Powder Chocolate, Sugar Free', 10, 'g', 30, 0, 7, 0, 0),
            ('Rice', 'Jasmine Rice, Microwaveable Bag', 250, 'g', 460, 9, 97, 4, 1),
            ('Potatoes', 'Kinder Pototoes, Frozen Precooked', 110, 'g', 110, 3, 23, 1, 2),
            ('Sweets & desserts', 'Lindt Dark Truffles', 3, 'ball', 220, 2, 12, 19, 1),
            ('Other dairy', 'Light Sour Cream', 30, 'g', 40, 2, 2, 2.5, 0),
            ('Oils & butter', 'Olive Oil Spray', 4, 'spray', 40, 0, 0, 4, 0),
            ('Oils & butter', 'Olive Oil', 15, 'ml', 120, 0, 0, 14, 0),
            ('Berries', 'Strawberries', 72, 'g', 23, 0, 6, 0, 1),
            ('Sauces & condiments', 'Ranch, Bolthouse Farms Cucumber', 30, 'g', 35, 1, 3, 2, 0),
            ('Sauces & condiments', 'Carolina Gold BBQ Sugar Free, G Hughes', 32, 'g', 15, 0, 2, 0, 0),
            ('Protein powders', 'Protein Powder, Casein (Legion)', 28, 'g', 100, 22, 2, 0, 0),
            ('Protein powders', 'Protein Powder, Casein (Optimum Nutrition)', 34, 'g', 120, 24, 4, 1, 1),
            ('Sweets & desserts', 'Pudding Chocolate, Sugar Free', 1, 'container', 70, 1, 14, 3.5, 2),
            ('Other supplements', 'Dextrose Powder', 20, 'g', 70, 0, 18, 0, 0),
            ('Other fruit', 'Dragon Fruit', 140, 'g', 80, 1, 20, 0.5, 5),
            ('Sweets & desserts', 'Legendary Donut Cinnamon', 2, 'donut', 160, 20, 25, 6, 8),
            ('Chips & crackers', 'Legendary Protein Chips', 1, 'bag', 150, 20, 4, 6, 1),
            ('Protein shakes', 'Muscle Milk', 1, 'carton', 160, 26, 11, 1.5, 0),
            ('Protein shakes', 'Muscle Milk Pro', 1, 'carton', 200, 33, 12, 2, 2),
            ('Flours & mixes', 'Oat Flour', 30, 'g', 110, 3, 21, 2, 3),
            ('Oats & cereal', 'Oatmeal', 40, 'g', 150, 5, 27, 2.5, 4),
            ('Protein shakes', 'Protein Shake, Oikos', 1, 'shake', 180, 30, 9, 4, 6),
            ('Other fruit', 'Orange', 96, 'g', 45, 0.9, 11, 0.1, 2.3),
            ('Nuts & seeds', 'PB2 Chocolate', 13, 'g', 50, 4, 6, 1, 1),
            ('Nuts & seeds', 'PB2', 13, 'g', 60, 6, 5, 1.5, 1),
            ('Nuts & seeds', 'Peanut Butter (Reduced Fat)', 36, 'g', 190, 7, 15, 12, 2),
            ('Protein bars', 'Protein Bar, Premier Cocoa Pebbles', 1, 'bar', 180, 20, 20, 3.5, 0),
            ('Protein bars', 'Protein Bar, Premier Peanut butter', 1, 'bar', 190, 19, 18, 7, 0),
            ('Protein powders', 'Protein Powder, ProJym Vanilla', 36, 'g', 140, 24, 5, 3, 0),
            ('Protein bars', 'Protein Bar, Quest Peanut Butter', 1, 'bar', 200, 18, 19, 12, 4),
            ('Chips & crackers', 'Protein Chips, Quest', 1, 'bag', 140, 20, 4, 4.5, 1),
            ('Berries', 'Raspberries', 140, 'g', 70, 2, 17, 1, 9),
            ('Protein bars', 'Protein Bar, Ready Brand', 1, 'bar', 200, 15, 28, 5, 7),
            ('Poultry', 'Realgood Foods Chicken Meatballs (Original)', 91, 'g', 110, 20, 2, 2.5, 0),
            ('Protein bars', 'Protein Bar, Quest Caramel Pecan', 1, 'bar', 170, 15, 29, 9, 11),
            ('Chips & crackers', 'Quest Cheezits Ranch', 1, 'bag', 130, 10, 10, 8, 5),
            ('Chips & crackers', 'Quest Cheezits', 1, 'bag', 130, 10, 10, 8, 5),
            ('Chips & crackers', 'Rice Cake Plain', 1, 'cake', 35, 0, 7, 0, 0),
            ('Chips & crackers', 'Rice Cake Cheddar', 1, 'cake', 60, 0, 9, 2, 0),
            ('Fish & seafood', 'Shrimp (Raw)', 4, 'oz', 132, 24.2, 1.8, 2, 0),
            ('Sauces & condiments', 'Salsa', 36, 'g', 10, 0.6, 2.4, 0.1, 0),
            ('Chips & crackers', 'Popcorn, Smartpop Small Bag', 1, 'bag', 100, 3, 23, 1.5, 4),
            ('Sauces & condiments', 'Maple Syrup, Sugar Free', 30, 'ml', 12, 0, 3, 0, 0),
            ('Sauces & condiments', 'BBQ Sauce, Sweet Baby Rays Sugar Free', 32, 'g', 15, 1, 4, 0, 0),
            ('Spices & mixes', 'Taco Seasoning', 1, 'packet', 75, 0, 15, 0, 0),
            ('Sweets & desserts', 'Yasso Fudge Bar', 1, 'bar', 100, 5, 19, 1, 0),
            ('Other fruit', 'Watermelon', 28, 'g', 9, 0.17, 2.14, 0.04, 0.12),
            ('Rice', 'White Rice (Dry)', 46, 'g', 170, 4, 38, 0, 0)
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
