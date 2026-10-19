/*
    Migration: 000007_create_standard_food (up)

    What:
        Creates the standard_food table: the starter list of foods with
        their serving size and macronutrients.

    Why:
        Every user gets their own editable copy of this list when their
        account is created (see 000010). Keeping the template in its own
        table means new users always start from the same, curated list.

    Notes:
        - Each food has one fixed serving, and the macros are for that
          serving (e.g. 100 g of chicken, or 1 tbsp of olive oil).
        - Serving units are metric or household measures only. The app
          converts grams to ounces for display.
*/

-- Create sequence
CREATE SEQUENCE seq_standard_food_standard_food_id AS INT
    INCREMENT BY 1
    MINVALUE 1
    START WITH 1
    NO CYCLE;

-- Create the table
CREATE TABLE standard_food (
    -- Fields
    standard_food_id INTEGER NOT NULL DEFAULT nextval('seq_standard_food_standard_food_id'),
    food_name VARCHAR(100) NOT NULL,
    category_id INTEGER NOT NULL,
    serving_size NUMERIC(8, 2) NOT NULL,
    serving_unit VARCHAR(20) NOT NULL,
    calories NUMERIC(7, 2) NOT NULL DEFAULT 0,
    protein_g NUMERIC(7, 2) NOT NULL DEFAULT 0,
    carbs_g NUMERIC(7, 2) NOT NULL DEFAULT 0,
    fat_g NUMERIC(7, 2) NOT NULL DEFAULT 0,
    fiber_g NUMERIC(7, 2) NOT NULL DEFAULT 0,
    -- Constraints
    CONSTRAINT pk_standard_food_standard_food_id PRIMARY KEY (standard_food_id),
    CONSTRAINT fk_standard_food_category_id FOREIGN KEY (category_id)
        REFERENCES food_category (category_id),
    CONSTRAINT unq_standard_food_food_name UNIQUE (food_name),
    CONSTRAINT chk_standard_food_serving_size CHECK (serving_size > 0),
    CONSTRAINT chk_standard_food_serving_unit
        CHECK (serving_unit IN ('g', 'ml', 'cup', 'tbsp', 'tsp', 'piece', 'slice', 'serving')),
    CONSTRAINT chk_standard_food_macros
        CHECK (calories >= 0 AND protein_g >= 0 AND carbs_g >= 0 AND fat_g >= 0 AND fiber_g >= 0)
);

ALTER SEQUENCE seq_standard_food_standard_food_id OWNED BY standard_food.standard_food_id;

-- Give grants
-- None needed: the master role owns the table.
