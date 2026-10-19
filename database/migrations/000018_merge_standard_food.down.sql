/*
    Migration: 000018_merge_standard_food (down)

    What:
        Puts standard_food back to the list from 000008, removes the
        categories added in the up migration, and reverts users' copies.

    Why:
        Reverts 000018_merge_standard_food.

    Notes:
        - Users' copies of the added foods are deleted if they were never
          edited or used. Otherwise they are kept as the user's own food
          (standard_food_id becomes NULL when the standard food is deleted).
        - Users' copies of replaced foods go back to the old values if they
          were not edited since (same serving-size safety rule as the up
          migration).
        - Removing the new categories fails if a user's food still uses
          one. Move those foods to another category first.
        - original_food and added_food are temporary working tables,
          dropped at the end.
*/

-- Old values of the replaced standard foods, keyed by their current name
CREATE TEMPORARY TABLE original_food (
    current_name VARCHAR(100) NOT NULL,
    food_name VARCHAR(100) NOT NULL,
    sub_category VARCHAR(50) NOT NULL,
    serving_size NUMERIC(8, 2) NOT NULL,
    serving_unit VARCHAR(20) NOT NULL,
    calories NUMERIC(7, 2) NOT NULL,
    protein_g NUMERIC(7, 2) NOT NULL,
    carbs_g NUMERIC(7, 2) NOT NULL,
    fat_g NUMERIC(7, 2) NOT NULL,
    fiber_g NUMERIC(7, 2) NOT NULL
);

INSERT INTO original_food (
    current_name,
    food_name,
    sub_category,
    serving_size,
    serving_unit,
    calories,
    protein_g,
    carbs_g,
    fat_g,
    fiber_g
)
VALUES
            ('Ground turkey, 93% lean (raw)', 'Ground turkey, 93% lean (raw)', 'Poultry', 100, 'g', 150, 18.7, 0, 8.3, 0),
            ('Chicken thigh, boneless skinless (raw)', 'Chicken thigh, boneless skinless (raw)', 'Poultry', 100, 'g', 120, 19.7, 0, 3.9, 0),
            ('Chicken breast, boneless skinless (raw)', 'Chicken breast, boneless skinless (raw)', 'Poultry', 100, 'g', 120, 22.5, 0, 2.6, 0),
            ('Ground beef, 96% lean (raw)', 'Ground beef, 96% lean (raw)', 'Beef', 100, 'g', 125, 21.5, 0, 4, 0),
            ('Ground beef, 93% lean (raw)', 'Ground beef, 93% lean (raw)', 'Beef', 100, 'g', 152, 20.9, 0, 7, 0),
            ('Cod (raw)', 'Cod (raw)', 'Fish & seafood', 100, 'g', 82, 17.8, 0, 0.7, 0),
            ('Shrimp', 'Shrimp (raw)', 'Fish & seafood', 100, 'g', 85, 20.1, 0, 0.5, 0),
            ('Egg whites (liquid)', 'Egg whites (liquid)', 'Eggs', 100, 'g', 52, 10.9, 0.7, 0.2, 0),
            ('Egg, large (whole)', 'Egg, large (whole)', 'Eggs', 1, 'piece', 72, 6.3, 0.4, 4.8, 0),
            ('Black beans, canned (drained)', 'Black beans, canned (drained)', 'Plant protein', 100, 'g', 91, 6, 16.6, 0.3, 6.9),
            ('White rice, long grain (dry)', 'White rice, long grain (dry)', 'Rice', 100, 'g', 365, 7.1, 80, 0.7, 1.3),
            ('Rolled oats (dry)', 'Rolled oats (dry)', 'Oats & cereal', 100, 'g', 379, 13.2, 67.7, 6.5, 10.1),
            ('Sweet potato (raw)', 'Sweet potato (raw)', 'Potatoes', 100, 'g', 86, 1.6, 20.1, 0.1, 3),
            ('Russet potato (raw)', 'Russet potato (raw)', 'Potatoes', 100, 'g', 79, 2.1, 18, 0.1, 1.3),
            ('Broccoli (raw)', 'Broccoli (raw)', 'Cruciferous', 100, 'g', 34, 2.8, 6.6, 0.4, 2.6),
            ('Asparagus (raw)', 'Asparagus (raw)', 'Other vegetables', 100, 'g', 20, 2.2, 3.9, 0.1, 2.1),
            ('Strawberries', 'Strawberries', 'Berries', 100, 'g', 32, 0.7, 7.7, 0.3, 2),
            ('Blueberries', 'Blueberries', 'Berries', 100, 'g', 57, 0.7, 14.5, 0.3, 2.4),
            ('Avocado', 'Avocado', 'Other fruit', 100, 'g', 160, 2, 8.5, 14.7, 6.7),
            ('Banana, medium', 'Banana, medium', 'Other fruit', 1, 'piece', 105, 1.3, 27, 0.4, 3.1),
            ('Greek yogurt, plain nonfat', 'Greek yogurt, plain nonfat', 'Yogurt', 100, 'g', 59, 10.2, 3.6, 0.4, 0),
            ('Mozzarella, part skim', 'Mozzarella, part skim', 'Cheese', 28, 'g', 72, 6.9, 0.8, 4.5, 0),
            ('Cheddar cheese', 'Cheddar cheese', 'Cheese', 28, 'g', 114, 7, 0.4, 9.4, 0),
            ('Peanut butter, smooth', 'Peanut butter, smooth', 'Nuts & seeds', 2, 'tbsp', 191, 7.1, 7.1, 16.4, 1.6),
            ('Taco seasoning', 'Taco seasoning', 'Spices & mixes', 2, 'tsp', 15, 0.3, 3, 0.2, 0.5),
            ('Salsa', 'Salsa', 'Sauces & condiments', 2, 'tbsp', 10, 0.5, 2, 0, 0.5),
            ('Cottage cheese, 2%', 'Cottage cheese, 2%', 'Yogurt', 100, 'g', 84, 11, 4.3, 2.3, 0);

-- Names of the standard foods the up migration added
CREATE TEMPORARY TABLE added_food (
    food_name VARCHAR(100) NOT NULL
);

INSERT INTO added_food (
    food_name
)
VALUES
            ('Cheese slice, 2% milk'),
            ('Bread, 35 calorie'),
            ('Bread, 45 calorie'),
            ('Dark chocolate, 72% (Ghirardelli)'),
            ('Almond milk'),
            ('American cheese'),
            ('Beef tenderloin steak'),
            ('Blackberries'),
            ('Ham, Black Forest'),
            ('Shrimp, black tiger'),
            ('Ranch dressing, cucumber (Bolthouse Farms)'),
            ('Bread, 35 calorie (alt)'),
            ('Canadian bacon (Sam''s Club)'),
            ('Tortilla, Carb Counter'),
            ('BBQ sauce, Carolina Gold sugar-free'),
            ('Casein protein powder (Legion)'),
            ('Casein protein powder (Optimum Nutrition)'),
            ('Cauliflower mash, chive'),
            ('Cauliflower mash, garlic'),
            ('Cauliflower mash'),
            ('Cauliflower rice'),
            ('Cheese stick'),
            ('Chicken breast, grilled (precooked)'),
            ('Chicken, lightly breaded'),
            ('Chicken, lightly breaded (higher fat)'),
            ('Chicken bites, grilled (Sam''s Club)'),
            ('Chicken bites, grilled (Tyson)'),
            ('Chicken sausage, apple'),
            ('Chicken thigh, boneless skinless (Sam''s Club)'),
            ('Chocolate pudding cup, sugar-free (Snack Pack)'),
            ('Plant-based chicken, Cajun (Daring)'),
            ('Plant-based chicken, lemon herb (Daring)'),
            ('Plant-based chicken, plain (Daring)'),
            ('Dark chocolate, 85%'),
            ('Dark chocolate chips'),
            ('Dextrose powder'),
            ('Dragon fruit'),
            ('Cheddar cheese, fat-free'),
            ('Cottage cheese, fat-free'),
            ('Shredded cheese, fiesta blend'),
            ('Filet steak'),
            ('Flank steak'),
            ('Strawberry banana mix (frozen)'),
            ('Top sirloin steak, grass-fed'),
            ('Greek yogurt (Oikos)'),
            ('Chicken breast, grilled (bagged)'),
            ('Chicken strips, grilled (Walmart)'),
            ('Ham, honey'),
            ('Jasmine rice, microwave (cooked)'),
            ('Pudding mix, chocolate (Jell-O)'),
            ('Pita bread (Joseph''s)'),
            ('Chicken breast, grilled (Sam''s Club)'),
            ('Gummy bears'),
            ('Pancake mix (Kodiak)'),
            ('Kidney beans'),
            ('Kiwi'),
            ('Potatoes (Kinder''s)'),
            ('Caesar dressing, light (Kraft)'),
            ('Protein donut, cinnamon (Legendary)'),
            ('Protein chips (Legendary)'),
            ('English muffin, light'),
            ('Sour cream, light'),
            ('Dark chocolate truffles (Lindt)'),
            ('Potatoes, little'),
            ('Lunch meat'),
            ('Cereal, cocoa (Magic Spoon)'),
            ('Mahi mahi'),
            ('Tortilla, mini (Mission)'),
            ('Tortilla (Mission)'),
            ('Tortilla, large (Mission)'),
            ('Protein shake (Muscle Milk)'),
            ('Protein shake, Pro (Muscle Milk)'),
            ('NY strip steak'),
            ('Olive oil spray (4 sec spray)'),
            ('Oat flour'),
            ('Oatmeal (dry)'),
            ('Protein shake (Oikos)'),
            ('Orange'),
            ('Turkey breast, oven roasted (deli)'),
            ('Protein shake (Owyn)'),
            ('Powdered peanut butter, chocolate (PB2)'),
            ('Powdered peanut butter (PB2)'),
            ('Peanut butter, reduced fat'),
            ('Peppers and onions'),
            ('Filet mignon, petite'),
            ('Pinto beans'),
            ('Plant protein powder'),
            ('Pork loin steak (Smithfield)'),
            ('Potatoes, garlic onion mix'),
            ('Protein cereal, chocolate (Premier Protein)'),
            ('Protein bar, Cocoa Pebbles (Premier Protein)'),
            ('Protein bar (Premier Protein)'),
            ('Soup, chicken noodle (Progresso)'),
            ('Soup, Santa Fe chicken (Progresso)'),
            ('Soup, chicken pot pie (Progresso)'),
            ('Soup, beef pot roast (Progresso)'),
            ('Soup, chicken & dumpling (Progresso)'),
            ('Whey protein powder'),
            ('Whey protein powder, zero carb'),
            ('Protein bar, caramel pecan (Quest)'),
            ('Protein crackers, ranch (Quest)'),
            ('Protein crackers (Quest)'),
            ('Protein snack, cookies & cream (Quest)'),
            ('Protein bar, chocolate peanut butter (Quest)'),
            ('Protein bar, cookies & cream (Quest)'),
            ('Protein chips (Quest)'),
            ('Raspberries'),
            ('Protein bar (Ready)'),
            ('Beef filet (Realgood Foods)'),
            ('Chicken meatballs (Realgood Foods)'),
            ('Refried pinto beans'),
            ('Ribeye steak'),
            ('Rice cake, plain'),
            ('Rice cake, cheddar'),
            ('Snack bar, dark chocolate sea salt (KIND)'),
            ('Sirloin tender steak'),
            ('Popcorn, small bag (SmartPop)'),
            ('Potatoes, smashed'),
            ('Steak strips'),
            ('Stir-fry steak'),
            ('Maple syrup, sugar-free'),
            ('BBQ sauce, sugar-free'),
            ('Turkey bacon'),
            ('Turkey bacon (alt)'),
            ('Turkey meatballs'),
            ('Turkey sausage patty'),
            ('Vegetable medley'),
            ('Frozen yogurt bar, fudge (Yasso)'),
            ('Chicken breast, grilled (Walmart)'),
            ('Watermelon'),
            ('White bread');

-- Delete users' copies of added foods that were never edited or used
DELETE FROM food AS f
USING standard_food AS sf
INNER JOIN added_food AS af
    ON af.food_name = sf.food_name
WHERE f.standard_food_id = sf.standard_food_id
    AND (f.food_name, f.category_id, f.serving_size, f.serving_unit, f.calories, f.protein_g, f.carbs_g, f.fat_g, f.fiber_g)
        = (sf.food_name, sf.category_id, sf.serving_size, sf.serving_unit, sf.calories, sf.protein_g, sf.carbs_g, sf.fat_g, sf.fiber_g)
    AND NOT EXISTS (
        SELECT 1
        FROM recipe_ingredient AS ri
        WHERE ri.food_id = f.food_id
    )
    AND NOT EXISTS (
        SELECT 1
        FROM food_log AS fl
        WHERE fl.food_id = f.food_id
    );

-- Revert users' unedited copies of replaced foods
UPDATE food AS f
SET
    food_name = ofd.food_name,
    category_id = fc.category_id,
    serving_size = ofd.serving_size,
    serving_unit = ofd.serving_unit,
    calories = ofd.calories,
    protein_g = ofd.protein_g,
    carbs_g = ofd.carbs_g,
    fat_g = ofd.fat_g,
    fiber_g = ofd.fiber_g
FROM standard_food AS sf
INNER JOIN original_food AS ofd
    ON ofd.current_name = sf.food_name
INNER JOIN food_category AS fc
    ON fc.category_name = ofd.sub_category
    AND fc.parent_category_id IS NOT NULL
WHERE f.standard_food_id = sf.standard_food_id
    AND f.is_active
    AND (f.food_name, f.category_id, f.serving_size, f.serving_unit, f.calories, f.protein_g, f.carbs_g, f.fat_g, f.fiber_g)
        = (sf.food_name, sf.category_id, sf.serving_size, sf.serving_unit, sf.calories, sf.protein_g, sf.carbs_g, sf.fat_g, sf.fiber_g)
    AND (
        (f.serving_size = ofd.serving_size AND f.serving_unit = ofd.serving_unit)
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
    AND NOT EXISTS (
        SELECT 1
        FROM food AS other
        WHERE other.user_id = f.user_id
            AND other.is_active
            AND other.food_id <> f.food_id
            AND other.food_name = ofd.food_name
    );

-- Restore the replaced standard foods
UPDATE standard_food AS sf
SET
    food_name = ofd.food_name,
    category_id = fc.category_id,
    serving_size = ofd.serving_size,
    serving_unit = ofd.serving_unit,
    calories = ofd.calories,
    protein_g = ofd.protein_g,
    carbs_g = ofd.carbs_g,
    fat_g = ofd.fat_g,
    fiber_g = ofd.fiber_g
FROM original_food AS ofd
INNER JOIN food_category AS fc
    ON fc.category_name = ofd.sub_category
    AND fc.parent_category_id IS NOT NULL
WHERE sf.food_name = ofd.current_name;

-- Remove the added standard foods (remaining user copies are detached)
DELETE FROM standard_food AS sf
USING added_food AS af
WHERE af.food_name = sf.food_name;

-- Remove the added categories, sub-categories first
DELETE FROM food_category
WHERE category_name IN (
    'Deli & breakfast meats',
    'Beans & legumes',
    'Flours & mixes',
    'Other dairy',
    'Protein powders',
    'Protein shakes',
    'Protein bars',
    'Other supplements',
    'Chips & crackers',
    'Snack bars',
    'Sweets & desserts',
    'Soups',
    'Prepared meals'
)
    AND parent_category_id IS NOT NULL;

DELETE FROM food_category
WHERE category_name IN (
    'Supplements',
    'Snacks & sweets',
    'Soups & prepared meals'
)
    AND parent_category_id IS NULL;

DROP TABLE original_food;

DROP TABLE added_food;
