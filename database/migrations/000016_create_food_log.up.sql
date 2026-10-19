/*
    Migration: 000016_create_food_log (up)

    What:
        Creates the food_log table: what a user ate on a given day, as a
        number of servings of either a food or a recipe.

    Why:
        The daily nutrition log lists these entries with their macros and
        a daily total. Macros are looked up from the food or recipe rather
        than copied, so fixing a food's numbers fixes the log too.

    Notes:
        - Exactly one of food_id or recipe_id must be set
          (chk_food_log_item).
        - The app only soft-deletes foods and recipes, so in practice they
          are only really deleted along with their user. The food and recipe
          foreign keys cascade so that deleting a user works no matter which
          order PostgreSQL runs the cascades in.
*/

-- Create sequence
CREATE SEQUENCE seq_food_log_food_log_id AS INT
    INCREMENT BY 1
    MINVALUE 1
    START WITH 1
    NO CYCLE;

-- Create the table
CREATE TABLE food_log (
    -- Fields
    food_log_id INTEGER NOT NULL DEFAULT nextval('seq_food_log_food_log_id'),
    user_id INTEGER NOT NULL,
    log_date DATE NOT NULL,
    food_id INTEGER,
    recipe_id INTEGER,
    servings NUMERIC(8, 3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    CONSTRAINT pk_food_log_food_log_id PRIMARY KEY (food_log_id),
    CONSTRAINT fk_food_log_user_id FOREIGN KEY (user_id)
        REFERENCES app_user (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_food_log_food_id FOREIGN KEY (food_id)
        REFERENCES food (food_id) ON DELETE CASCADE,
    CONSTRAINT fk_food_log_recipe_id FOREIGN KEY (recipe_id)
        REFERENCES recipe (recipe_id) ON DELETE CASCADE,
    CONSTRAINT chk_food_log_item CHECK (num_nonnulls(food_id, recipe_id) = 1),
    CONSTRAINT chk_food_log_servings CHECK (servings > 0)
);

ALTER SEQUENCE seq_food_log_food_log_id OWNED BY food_log.food_log_id;

-- Create indexes
CREATE INDEX idx_food_log_user_id_log_date ON food_log (user_id, log_date);

CREATE INDEX idx_food_log_food_id ON food_log (food_id);

CREATE INDEX idx_food_log_recipe_id ON food_log (recipe_id);

-- Trigger assignments
CREATE TRIGGER trg_food_log_set_updated_at
    BEFORE UPDATE ON food_log
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_set_updated_at();

-- Give grants
-- None needed: the master role owns the table.
