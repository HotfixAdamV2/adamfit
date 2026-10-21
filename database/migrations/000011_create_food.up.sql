/*
    Migration: 000011_create_food (up)

    What:
        Creates the food table: each user's own, fully editable list of
        foods with a serving size and the macronutrients for that serving.

    Why:
        Users build recipes from, and log meals against, their own food
        list. Each user starts with a copy of standard_food (see 000012)
        and can then add, edit or remove foods freely.

    Notes:
        - Deleting a food in the app sets is_active to FALSE instead of
          removing the row, so recipes and past log entries that use it
          keep working.
        - Food names are unique per user among active foods only, so a
          removed food's name can be reused. That needs a partial unique
          index, because constraints cannot have a WHERE clause.
        - standard_food_id records which standard food a row was copied
          from (NULL for foods the user created).
        - serving_unit must be a unit_code in serving_unit (000007), with
          ON UPDATE CASCADE, the same as standard_food.
*/

-- Create sequence
CREATE SEQUENCE seq_food_food_id AS INT
    INCREMENT BY 1
    MINVALUE 1
    START WITH 1
    NO CYCLE;

-- Create the table
CREATE TABLE food (
    -- Fields
    food_id INTEGER NOT NULL DEFAULT nextval('seq_food_food_id'),
    user_id INTEGER NOT NULL,
    food_name VARCHAR(100) NOT NULL,
    category_id INTEGER NOT NULL,
    serving_size NUMERIC(8, 2) NOT NULL,
    serving_unit VARCHAR(20) NOT NULL,
    calories NUMERIC(7, 2) NOT NULL DEFAULT 0,
    protein_g NUMERIC(7, 2) NOT NULL DEFAULT 0,
    carbs_g NUMERIC(7, 2) NOT NULL DEFAULT 0,
    fat_g NUMERIC(7, 2) NOT NULL DEFAULT 0,
    fiber_g NUMERIC(7, 2) NOT NULL DEFAULT 0,
    standard_food_id INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    CONSTRAINT pk_food_food_id PRIMARY KEY (food_id),
    CONSTRAINT fk_food_user_id FOREIGN KEY (user_id)
        REFERENCES app_user (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_food_category_id FOREIGN KEY (category_id)
        REFERENCES food_category (category_id),
    CONSTRAINT fk_food_serving_unit FOREIGN KEY (serving_unit)
        REFERENCES serving_unit (unit_code) ON UPDATE CASCADE,
    CONSTRAINT fk_food_standard_food_id FOREIGN KEY (standard_food_id)
        REFERENCES standard_food (standard_food_id) ON DELETE SET NULL,
    CONSTRAINT chk_food_food_name CHECK (LENGTH(TRIM(food_name)) > 0),
    CONSTRAINT chk_food_serving_size CHECK (serving_size > 0),
    CONSTRAINT chk_food_macros
        CHECK (calories >= 0 AND protein_g >= 0 AND carbs_g >= 0 AND fat_g >= 0 AND fiber_g >= 0)
);

ALTER SEQUENCE seq_food_food_id OWNED BY food.food_id;

-- Create indexes
CREATE UNIQUE INDEX unq_food_user_id_food_name ON food (user_id, food_name)
    WHERE is_active;

CREATE INDEX idx_food_user_id ON food (user_id);

-- Trigger assignments
CREATE TRIGGER trg_food_set_updated_at
    BEFORE UPDATE ON food
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_set_updated_at();

-- Give grants
-- None needed: the master role owns the table.
