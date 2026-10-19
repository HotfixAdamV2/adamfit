/*
    Migration: 000018_merge_standard_food (up)

    What:
        Merges Adam's own food list (the Foods sheet of
        nutrition_converted.xlsx) into standard_food, adds the categories
        those foods need, and brings every user's copy up to date.

    Why:
        The starter list should hold the foods Adam actually eats, with the
        label values he already uses, alongside the generic foods from
        000008.

    Notes:
        - Where both lists had the same food (e.g. chicken breast), the
          spreadsheet's values replace the old standard food's. The row is
          updated in place, so users' copies stay linked to it.
        - Everything else in the sheet is added. "English Muffin Light" was
          left out because it is an exact copy of "Light English Muffin".
        - Names were rewritten in the standard list's style: sentence case,
          the generic food first, qualifiers after a comma, and state or
          brand in brackets (e.g. "Protein bar, caramel pecan (Quest)").
        - Two calorie values in the sheet did not match their macros and
          were recalculated as 9 x fat + 4 x carbs + 4 x protein:
          Cheddar cheese (180 -> 113) and Ribeye steak (200 -> 280).
        - A user's copy of a replaced food is only refreshed if they never
          edited it (it still matches the old standard values). If the
          serving size changes, the copy must also be unused by recipes and
          the log, because changing the serving would change the meaning
          of servings already recorded.
        - Every user gets the newly added foods, except where they already
          have an active food with the same name.
        - merge_food and old_standard_food are temporary working tables,
          dropped at the end.
*/

-- New top-level categories
INSERT INTO food_category (
    category_name,
    sort_order
)
VALUES
    ('Supplements', 8),
    ('Snacks & sweets', 9),
    ('Soups & prepared meals', 10);

-- New sub-categories
WITH
    sub_category (parent_name, category_name, sort_order) AS (
        VALUES
            ('Protein', 'Deli & breakfast meats', 7),
            ('Protein', 'Beans & legumes', 8),
            ('Grains & starches', 'Flours & mixes', 6),
            ('Dairy', 'Other dairy', 4),
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

-- The foods from the spreadsheet (macros are per serving).
-- replaces_food_name is the old standard food it replaces, if any.
CREATE TEMPORARY TABLE merge_food (
    sub_category VARCHAR(50) NOT NULL,
    food_name VARCHAR(100) NOT NULL,
    serving_size NUMERIC(8, 2) NOT NULL,
    serving_unit VARCHAR(20) NOT NULL,
    calories NUMERIC(7, 2) NOT NULL,
    protein_g NUMERIC(7, 2) NOT NULL,
    carbs_g NUMERIC(7, 2) NOT NULL,
    fat_g NUMERIC(7, 2) NOT NULL,
    fiber_g NUMERIC(7, 2) NOT NULL,
    replaces_food_name VARCHAR(100)
);

INSERT INTO merge_food (
    sub_category,
    food_name,
    serving_size,
    serving_unit,
    calories,
    protein_g,
    carbs_g,
    fat_g,
    fiber_g,
    replaces_food_name
)
VALUES
            ('Cheese', 'Cheese slice, 2% milk', 1, 'slice', 45, 4, 2, 2.5, 0, NULL),
            ('Bread & tortillas', 'Bread, 35 calorie', 1, 'slice', 30, 2, 8, 0.5, 1.5, NULL),
            ('Bread & tortillas', 'Bread, 45 calorie', 1, 'slice', 45, 2.5, 8, 0.5, 1.5, NULL),
            ('Sweets & desserts', 'Dark chocolate, 72% (Ghirardelli)', 25, 'g', 130, 2, 11, 11, 3, NULL),
            ('Beef', 'Ground beef, 93% lean (raw)', 4, 'oz', 170, 23, 0, 8, 0, 'Ground beef, 93% lean (raw)'),
            ('Beef', 'Ground beef, 96% lean (raw)', 4, 'oz', 140, 24, 0, 4.5, 0, 'Ground beef, 96% lean (raw)'),
            ('Poultry', 'Ground turkey, 93% lean (raw)', 4, 'oz', 160, 22, 0, 8, 0, 'Ground turkey, 93% lean (raw)'),
            ('Milk', 'Almond milk', 8, 'fl oz', 30, 1, 1, 2.5, 1, NULL),
            ('Cheese', 'American cheese', 1, 'slice', 50, 3, 2, 3.5, 0, NULL),
            ('Other vegetables', 'Asparagus (raw)', 84, 'g', 15, 2, 3, 0, 2, 'Asparagus (raw)'),
            ('Other fruit', 'Avocado', 100, 'g', 160, 2, 8.5, 14.7, 6.7, 'Avocado'),
            ('Other fruit', 'Banana, medium', 118, 'g', 105, 1.3, 27, 0.4, 3.1, 'Banana, medium'),
            ('Beef', 'Beef tenderloin steak', 4, 'oz', 160, 24, 0, 7, 0, NULL),
            ('Berries', 'Blackberries', 144, 'g', 60, 2, 14, 0, 8, NULL),
            ('Beans & legumes', 'Black beans, canned (drained)', 130, 'g', 130, 8, 23, 0.5, 6, 'Black beans, canned (drained)'),
            ('Deli & breakfast meats', 'Ham, Black Forest', 2, 'slice', 60, 10, 2, 1.5, 0, NULL),
            ('Fish & seafood', 'Shrimp, black tiger', 4, 'oz', 80, 19, 0, 0.5, 0, NULL),
            ('Berries', 'Blueberries', 140, 'g', 70, 1, 17, 1, 4, 'Blueberries'),
            ('Sauces & condiments', 'Ranch dressing, cucumber (Bolthouse Farms)', 30, 'g', 35, 1, 3, 2, 0, NULL),
            ('Bread & tortillas', 'Bread, 35 calorie (alt)', 1, 'slice', 37, 1.7, 8, 0.5, 1.7, NULL),
            ('Cruciferous', 'Broccoli (raw)', 148, 'g', 50, 4.2, 10, 0.5, 3.8, 'Broccoli (raw)'),
            ('Deli & breakfast meats', 'Canadian bacon (Sam''s Club)', 3, 'slice', 60, 12, 2, 1, 0, NULL),
            ('Bread & tortillas', 'Tortilla, Carb Counter', 1, 'piece', 60, 4, 13, 1.5, 12, NULL),
            ('Sauces & condiments', 'BBQ sauce, Carolina Gold sugar-free', 32, 'g', 15, 0, 2, 0, 0, NULL),
            ('Protein powders', 'Casein protein powder (Legion)', 28, 'g', 100, 22, 2, 0, 0, NULL),
            ('Protein powders', 'Casein protein powder (Optimum Nutrition)', 34, 'g', 120, 24, 4, 1, 1, NULL),
            ('Cruciferous', 'Cauliflower mash, chive', 0.5, 'cup', 70, 2, 9, 3.5, 2, NULL),
            ('Cruciferous', 'Cauliflower mash, garlic', 1, 'container', 120, 3, 19, 3, 6, NULL),
            ('Cruciferous', 'Cauliflower mash', 1, 'container', 90, 3, 19, 1.5, 6, NULL),
            ('Cruciferous', 'Cauliflower rice', 76, 'g', 15, 1, 3, 0, 2, NULL),
            ('Fish & seafood', 'Cod (raw)', 4, 'oz', 80, 17, 0, 1, 0, 'Cod (raw)'),
            ('Cheese', 'Cheddar cheese', 28, 'g', 113, 6, 2, 9, 0, 'Cheddar cheese'),
            ('Cheese', 'Cheese stick', 1, 'piece', 50, 6, 1, 2.5, 0, NULL),
            ('Poultry', 'Chicken breast, grilled (precooked)', 136, 'g', 280, 44, 2, 11, 0, NULL),
            ('Poultry', 'Chicken, lightly breaded', 4, 'oz', 130, 23, 4, 2, 1, NULL),
            ('Poultry', 'Chicken, lightly breaded (higher fat)', 4, 'oz', 180, 23, 5, 7, 1, NULL),
            ('Poultry', 'Chicken bites, grilled (Sam''s Club)', 3, 'oz', 110, 16, 2, 3.5, 0, NULL),
            ('Poultry', 'Chicken bites, grilled (Tyson)', 3, 'oz', 130, 20, 2, 4, 0, NULL),
            ('Poultry', 'Chicken breast, boneless skinless (raw)', 4, 'oz', 120, 25, 0, 1.5, 0, 'Chicken breast, boneless skinless (raw)'),
            ('Deli & breakfast meats', 'Chicken sausage, apple', 1, 'piece', 110, 13, 2, 6, 0, NULL),
            ('Poultry', 'Chicken thigh, boneless skinless (Sam''s Club)', 4, 'oz', 180, 25, 0, 8.5, 0, NULL),
            ('Poultry', 'Chicken thigh, boneless skinless (raw)', 4, 'oz', 210, 26, 0, 10, 0, 'Chicken thigh, boneless skinless (raw)'),
            ('Sweets & desserts', 'Chocolate pudding cup, sugar-free (Snack Pack)', 92, 'g', 70, 1, 14, 3.5, 2, NULL),
            ('Plant protein', 'Plant-based chicken, Cajun (Daring)', 3, 'oz', 110, 13, 6, 3.5, 4, NULL),
            ('Plant protein', 'Plant-based chicken, lemon herb (Daring)', 2.5, 'oz', 100, 13, 6, 2, 4, NULL),
            ('Plant protein', 'Plant-based chicken, plain (Daring)', 2.5, 'oz', 90, 14, 5, 2, 5, NULL),
            ('Sweets & desserts', 'Dark chocolate, 85%', 30, 'g', 170, 4, 11, 14, 4, NULL),
            ('Sweets & desserts', 'Dark chocolate chips', 15, 'g', 60, 1, 9, 4.5, 5, NULL),
            ('Other supplements', 'Dextrose powder', 20, 'g', 70, 0, 18, 0, 0, NULL),
            ('Other fruit', 'Dragon fruit', 140, 'g', 80, 1, 20, 0.5, 5, NULL),
            ('Eggs', 'Egg whites (liquid)', 46, 'g', 25, 5, 1, 0, 0, 'Egg whites (liquid)'),
            ('Eggs', 'Egg, large (whole)', 1, 'piece', 75, 7, 0, 5, 0, 'Egg, large (whole)'),
            ('Cheese', 'Cheddar cheese, fat-free', 28, 'g', 45, 9, 2, 0, 0, NULL),
            ('Other dairy', 'Cottage cheese, fat-free', 113, 'g', 80, 12, 6, 0, 0, NULL),
            ('Cheese', 'Shredded cheese, fiesta blend', 28, 'g', 90, 7, 2, 6, 0, NULL),
            ('Beef', 'Filet steak', 4, 'oz', 180, 25, 0, 8, 0, NULL),
            ('Beef', 'Flank steak', 4, 'oz', 180, 24, 0, 9, 0, NULL),
            ('Berries', 'Strawberry banana mix (frozen)', 140, 'g', 80, 0, 20, 0, 3, NULL),
            ('Beef', 'Top sirloin steak, grass-fed', 4, 'oz', 150, 25, 0, 5, 0, NULL),
            ('Yogurt', 'Greek yogurt (Oikos)', 1, 'container', 90, 15, 7, 0, 0, NULL),
            ('Yogurt', 'Greek yogurt, plain nonfat', 170, 'g', 100, 17, 9, 0, 0, 'Greek yogurt, plain nonfat'),
            ('Poultry', 'Chicken breast, grilled (bagged)', 3, 'oz', 90, 17, 0, 2, 0, NULL),
            ('Poultry', 'Chicken strips, grilled (Walmart)', 3, 'oz', 100, 19, 2, 1.5, 0, NULL),
            ('Deli & breakfast meats', 'Ham, honey', 2, 'slice', 70, 11, 5, 1.5, 0, NULL),
            ('Rice', 'Jasmine rice, microwave (cooked)', 250, 'g', 460, 9, 97, 4, 1, NULL),
            ('Sweets & desserts', 'Pudding mix, chocolate (Jell-O)', 10, 'g', 30, 0, 7, 0, 0, NULL),
            ('Bread & tortillas', 'Pita bread (Joseph''s)', 1, 'piece', 70, 6, 12, 2, 6, NULL),
            ('Poultry', 'Chicken breast, grilled (Sam''s Club)', 132, 'g', 280, 44, 2, 11, 0, NULL),
            ('Sweets & desserts', 'Gummy bears', 30, 'g', 100, 2, 23, 0, 0, NULL),
            ('Flours & mixes', 'Pancake mix (Kodiak)', 63, 'g', 220, 15, 37, 2.5, 5, NULL),
            ('Beans & legumes', 'Kidney beans', 130, 'g', 110, 7, 19, 0, 7, NULL),
            ('Other fruit', 'Kiwi', 69, 'g', 42, 0.8, 10, 0.4, 2.1, NULL),
            ('Potatoes', 'Potatoes (Kinder''s)', 110, 'g', 110, 3, 23, 1, 2, NULL),
            ('Sauces & condiments', 'Caesar dressing, light (Kraft)', 32, 'g', 35, 1, 4, 2, 0, NULL),
            ('Sweets & desserts', 'Protein donut, cinnamon (Legendary)', 2, 'piece', 160, 20, 25, 6, 8, NULL),
            ('Chips & crackers', 'Protein chips (Legendary)', 1, 'bag', 150, 20, 4, 6, 1, NULL),
            ('Bread & tortillas', 'English muffin, light', 1, 'piece', 100, 4, 26, 1, 8, NULL),
            ('Other dairy', 'Sour cream, light', 28, 'g', 40, 2, 2, 2.5, 0, NULL),
            ('Sweets & desserts', 'Dark chocolate truffles (Lindt)', 3, 'piece', 220, 2, 12, 19, 1, NULL),
            ('Potatoes', 'Potatoes, little', 110, 'g', 80, 2, 16, 0, 2, NULL),
            ('Deli & breakfast meats', 'Lunch meat', 2, 'oz', 60, 11, 0, 1.5, 0, NULL),
            ('Oats & cereal', 'Cereal, cocoa (Magic Spoon)', 37, 'g', 140, 13, 15, 7, 2, NULL),
            ('Fish & seafood', 'Mahi mahi', 3, 'oz', 92, 20, 0, 1.5, 0, NULL),
            ('Bread & tortillas', 'Tortilla, mini (Mission)', 3, 'piece', 110, 7, 19, 5, 19, NULL),
            ('Bread & tortillas', 'Tortilla (Mission)', 1, 'piece', 60, 4, 13, 1.5, 12, NULL),
            ('Bread & tortillas', 'Tortilla, large (Mission)', 1, 'piece', 90, 5, 23, 2, 18, NULL),
            ('Protein shakes', 'Protein shake (Muscle Milk)', 1, 'container', 160, 26, 11, 1.5, 0, NULL),
            ('Protein shakes', 'Protein shake, Pro (Muscle Milk)', 1, 'container', 200, 33, 12, 2, 2, NULL),
            ('Beef', 'NY strip steak', 4, 'oz', 352, 29.3, 0, 25.3, 0, NULL),
            ('Oils & butter', 'Olive oil spray (4 sec spray)', 1, 'serving', 40, 0, 0, 4, 0, NULL),
            ('Flours & mixes', 'Oat flour', 30, 'g', 110, 3, 21, 2, 3, NULL),
            ('Oats & cereal', 'Oatmeal (dry)', 40, 'g', 150, 5, 27, 2.5, 4, NULL),
            ('Protein shakes', 'Protein shake (Oikos)', 1, 'container', 180, 30, 9, 4, 6, NULL),
            ('Other fruit', 'Orange', 96, 'g', 45, 0.9, 11, 0.1, 2.3, NULL),
            ('Deli & breakfast meats', 'Turkey breast, oven roasted (deli)', 2, 'oz', 50, 9, 2, 1, 0, NULL),
            ('Protein shakes', 'Protein shake (Owyn)', 1, 'container', 200, 32, 6, 6, 6, NULL),
            ('Nuts & seeds', 'Powdered peanut butter, chocolate (PB2)', 13, 'g', 50, 4, 6, 1, 1, NULL),
            ('Nuts & seeds', 'Powdered peanut butter (PB2)', 13, 'g', 60, 6, 5, 1.5, 1, NULL),
            ('Nuts & seeds', 'Peanut butter, smooth', 32, 'g', 188, 7, 7.7, 16, 0, 'Peanut butter, smooth'),
            ('Nuts & seeds', 'Peanut butter, reduced fat', 36, 'g', 190, 7, 15, 12, 2, NULL),
            ('Other vegetables', 'Peppers and onions', 85, 'g', 20, 1, 4, 0, 1, NULL),
            ('Beef', 'Filet mignon, petite', 4, 'oz', 180, 25, 0, 8, 0, NULL),
            ('Beans & legumes', 'Pinto beans', 130, 'g', 110, 7, 20, 0, 5, NULL),
            ('Protein powders', 'Plant protein powder', 40, 'g', 150, 24, 6, 3.5, 2, NULL),
            ('Pork', 'Pork loin steak (Smithfield)', 4, 'oz', 110, 20, 2, 2, 0, NULL),
            ('Potatoes', 'Russet potato (raw)', 148, 'g', 110, 3, 26, 0, 2, 'Russet potato (raw)'),
            ('Potatoes', 'Potatoes, garlic onion mix', 113, 'g', 110, 2, 19, 2.5, 2, NULL),
            ('Oats & cereal', 'Protein cereal, chocolate (Premier Protein)', 42, 'g', 180, 20, 14, 5, 2, NULL),
            ('Protein bars', 'Protein bar, Cocoa Pebbles (Premier Protein)', 1, 'bar', 180, 20, 20, 3.5, 0, NULL),
            ('Protein bars', 'Protein bar (Premier Protein)', 1, 'bar', 190, 19, 18, 7, 0, NULL),
            ('Soups', 'Soup, chicken noodle (Progresso)', 1, 'can', 130, 11, 19, 1.5, 2, NULL),
            ('Soups', 'Soup, Santa Fe chicken (Progresso)', 1, 'can', 160, 11, 29, 2.5, 8, NULL),
            ('Soups', 'Soup, chicken pot pie (Progresso)', 1, 'can', 190, 9, 31, 4, 2, NULL),
            ('Soups', 'Soup, beef pot roast (Progresso)', 1, 'can', 150, 11, 20, 2.5, 3, NULL),
            ('Soups', 'Soup, chicken & dumpling (Progresso)', 1, 'can', 160, 11, 23, 2.5, 3, NULL),
            ('Protein powders', 'Whey protein powder', 35, 'g', 130, 25, 3, 2, 1, NULL),
            ('Protein powders', 'Whey protein powder, zero carb', 31, 'g', 110, 25, 0, 0.5, 0, NULL),
            ('Protein bars', 'Protein bar, caramel pecan (Quest)', 1, 'bar', 170, 15, 29, 9, 11, NULL),
            ('Chips & crackers', 'Protein crackers, ranch (Quest)', 1, 'bag', 130, 10, 10, 8, 5, NULL),
            ('Chips & crackers', 'Protein crackers (Quest)', 1, 'bag', 130, 10, 10, 8, 5, NULL),
            ('Protein bars', 'Protein snack, cookies & cream (Quest)', 1, 'bar', 150, 16, 23, 6, 6, NULL),
            ('Protein bars', 'Protein bar, chocolate peanut butter (Quest)', 1, 'bar', 200, 18, 19, 12, 4, NULL),
            ('Protein bars', 'Protein bar, cookies & cream (Quest)', 1, 'bar', 190, 21, 22, 9, 13, NULL),
            ('Chips & crackers', 'Protein chips (Quest)', 1, 'bag', 140, 20, 4, 4.5, 1, NULL),
            ('Berries', 'Raspberries', 140, 'g', 70, 2, 17, 1, 9, NULL),
            ('Protein bars', 'Protein bar (Ready)', 1, 'bar', 200, 15, 28, 5, 7, NULL),
            ('Prepared meals', 'Beef filet (Realgood Foods)', 103, 'g', 140, 20, 5, 4, 1, NULL),
            ('Prepared meals', 'Chicken meatballs (Realgood Foods)', 91, 'g', 110, 20, 2, 2.5, 0, NULL),
            ('Beans & legumes', 'Refried pinto beans', 130, 'g', 80, 4, 16, 0, 5, NULL),
            ('Beef', 'Ribeye steak', 4, 'oz', 280, 24, 1, 20, 0, NULL),
            ('Chips & crackers', 'Rice cake, plain', 1, 'piece', 35, 0, 7, 0, 0, NULL),
            ('Chips & crackers', 'Rice cake, cheddar', 1, 'piece', 60, 0, 9, 2, 0, NULL),
            ('Sauces & condiments', 'Salsa', 36, 'g', 10, 0.6, 2.4, 0.1, 0, 'Salsa'),
            ('Snack bars', 'Snack bar, dark chocolate sea salt (KIND)', 1, 'bar', 180, 6, 16, 15, 7, NULL),
            ('Beef', 'Sirloin tender steak', 4, 'oz', 175, 25, 0, 8, 0, NULL),
            ('Fish & seafood', 'Shrimp', 4, 'oz', 132, 24.2, 1.8, 2, 0, 'Shrimp (raw)'),
            ('Cheese', 'Mozzarella, part skim', 28, 'g', 80, 8, 2, 4, 0, 'Mozzarella, part skim'),
            ('Chips & crackers', 'Popcorn, small bag (SmartPop)', 1, 'bag', 100, 3, 23, 1.5, 4, NULL),
            ('Potatoes', 'Potatoes, smashed', 110, 'g', 110, 3, 23, 1, 2, NULL),
            ('Beef', 'Steak strips', 3, 'oz', 120, 17, 4, 3.5, 0, NULL),
            ('Beef', 'Stir-fry steak', 4, 'oz', 150, 25, 0, 6, 0, NULL),
            ('Berries', 'Strawberries', 72, 'g', 23, 0, 6, 0, 1, 'Strawberries'),
            ('Sauces & condiments', 'Maple syrup, sugar-free', 30, 'ml', 12, 0, 3, 0, 0, NULL),
            ('Sauces & condiments', 'BBQ sauce, sugar-free', 32, 'g', 15, 1, 4, 0, 0, NULL),
            ('Potatoes', 'Sweet potato (raw)', 130, 'g', 100, 2, 23, 0, 4, 'Sweet potato (raw)'),
            ('Spices & mixes', 'Taco seasoning', 25, 'g', 75, 0, 15, 0, 0, 'Taco seasoning'),
            ('Deli & breakfast meats', 'Turkey bacon', 2, 'slice', 50, 6, 1, 2.5, 0, NULL),
            ('Deli & breakfast meats', 'Turkey bacon (alt)', 1, 'slice', 45, 5, 1, 2.5, 0, NULL),
            ('Poultry', 'Turkey meatballs', 140, 'g', 140, 14, 6, 9, 2, NULL),
            ('Deli & breakfast meats', 'Turkey sausage patty', 2, 'piece', 110, 11, 1, 7, 0, NULL),
            ('Other vegetables', 'Vegetable medley', 85, 'g', 45, 2, 10, 0, 3, NULL),
            ('Sweets & desserts', 'Frozen yogurt bar, fudge (Yasso)', 1, 'bar', 100, 5, 19, 1, 0, NULL),
            ('Poultry', 'Chicken breast, grilled (Walmart)', 4.5, 'oz', 240, 37, 2, 9, 0, NULL),
            ('Other fruit', 'Watermelon', 1, 'oz', 9, 0.17, 2.14, 0.04, 0.12, NULL),
            ('Bread & tortillas', 'White bread', 2, 'slice', 150, 5, 28, 2, 2, NULL),
            ('Rice', 'White rice, long grain (dry)', 46, 'g', 170, 4, 38, 0, 0, 'White rice, long grain (dry)'),
            ('Oats & cereal', 'Rolled oats (dry)', 40, 'g', 150, 5, 27, 2.5, 4, 'Rolled oats (dry)');

-- Snapshot of the standard foods before any changes, used to spot user
-- copies that were never edited
CREATE TEMPORARY TABLE old_standard_food AS
SELECT *
FROM standard_food;

-- Replace overlapping standard foods in place
UPDATE standard_food AS sf
SET
    food_name = mf.food_name,
    category_id = fc.category_id,
    serving_size = mf.serving_size,
    serving_unit = mf.serving_unit,
    calories = mf.calories,
    protein_g = mf.protein_g,
    carbs_g = mf.carbs_g,
    fat_g = mf.fat_g,
    fiber_g = mf.fiber_g
FROM merge_food AS mf
INNER JOIN food_category AS fc
    ON fc.category_name = mf.sub_category
    AND fc.parent_category_id IS NOT NULL
WHERE sf.food_name = mf.replaces_food_name;

-- Add the new standard foods
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
    mf.food_name,
    fc.category_id,
    mf.serving_size,
    mf.serving_unit,
    mf.calories,
    mf.protein_g,
    mf.carbs_g,
    mf.fat_g,
    mf.fiber_g
FROM merge_food AS mf
INNER JOIN food_category AS fc
    ON fc.category_name = mf.sub_category
    AND fc.parent_category_id IS NOT NULL
WHERE mf.replaces_food_name IS NULL;

-- Cottage cheese belongs in the new Other dairy sub-category
UPDATE standard_food
SET category_id = (
    SELECT category_id
    FROM food_category
    WHERE category_name = 'Other dairy'
)
WHERE food_name = 'Cottage cheese, 2%';

-- Refresh users' unedited copies of changed standard foods
UPDATE food AS f
SET
    food_name = sf.food_name,
    category_id = sf.category_id,
    serving_size = sf.serving_size,
    serving_unit = sf.serving_unit,
    calories = sf.calories,
    protein_g = sf.protein_g,
    carbs_g = sf.carbs_g,
    fat_g = sf.fat_g,
    fiber_g = sf.fiber_g
FROM standard_food AS sf
INNER JOIN old_standard_food AS old
    ON old.standard_food_id = sf.standard_food_id
WHERE f.standard_food_id = sf.standard_food_id
    AND f.is_active
    -- The copy still matches the old standard food, so it was never edited
    AND (f.food_name, f.category_id, f.serving_size, f.serving_unit, f.calories, f.protein_g, f.carbs_g, f.fat_g, f.fiber_g)
        = (old.food_name, old.category_id, old.serving_size, old.serving_unit, old.calories, old.protein_g, old.carbs_g, old.fat_g, old.fiber_g)
    -- The standard food actually changed
    AND (sf.food_name, sf.category_id, sf.serving_size, sf.serving_unit, sf.calories, sf.protein_g, sf.carbs_g, sf.fat_g, sf.fiber_g)
        IS DISTINCT FROM (old.food_name, old.category_id, old.serving_size, old.serving_unit, old.calories, old.protein_g, old.carbs_g, old.fat_g, old.fiber_g)
    -- A new serving size is only safe if no recipe or log entry uses the food
    AND (
        (f.serving_size = sf.serving_size AND f.serving_unit = sf.serving_unit)
        OR NOT (
            EXISTS (
                SELECT 1
                FROM recipe_ingredient AS ri
                WHERE ri.food_id = f.food_id
            )
            OR EXISTS (
                SELECT 1
                FROM food_log AS fl
                WHERE fl.food_id = f.food_id
            )
        )
    )
    -- The user does not already have another food with the new name
    AND NOT EXISTS (
        SELECT 1
        FROM food AS other
        WHERE other.user_id = f.user_id
            AND other.is_active
            AND other.food_id <> f.food_id
            AND other.food_name = sf.food_name
    );

-- Give every user the newly added foods
INSERT INTO food (
    user_id,
    food_name,
    category_id,
    serving_size,
    serving_unit,
    calories,
    protein_g,
    carbs_g,
    fat_g,
    fiber_g,
    standard_food_id
)
SELECT
    au.user_id,
    sf.food_name,
    sf.category_id,
    sf.serving_size,
    sf.serving_unit,
    sf.calories,
    sf.protein_g,
    sf.carbs_g,
    sf.fat_g,
    sf.fiber_g,
    sf.standard_food_id
FROM app_user AS au
CROSS JOIN standard_food AS sf
WHERE NOT EXISTS (
        SELECT 1
        FROM old_standard_food AS old
        WHERE old.standard_food_id = sf.standard_food_id
    )
    AND NOT EXISTS (
        SELECT 1
        FROM food AS f
        WHERE f.user_id = au.user_id
            AND f.is_active
            AND f.food_name = sf.food_name
    );

DROP TABLE merge_food;

DROP TABLE old_standard_food;
