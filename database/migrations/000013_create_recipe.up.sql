/*
    Migration: 000013_create_recipe (up)

    What:
        Creates the recipe table: a user's named meal (e.g. "Chicken and
        rice") with its yield and cooking instructions.

    Why:
        Recipes combine foods from the user's food list (see
        recipe_ingredient) so a whole meal can be logged in one step.

    Notes:
        - servings_per_recipe is how many servings the whole recipe makes.
          Per-serving macros are the ingredient totals divided by it (see
          vw_recipe_nutrition). serving_label names one serving, e.g.
          "bowl" or "serving".
        - Like food, deleting a recipe in the app sets is_active to FALSE
          so past log entries keep working, and names are unique per user
          among active recipes only.
*/

-- Create sequence
CREATE SEQUENCE seq_recipe_recipe_id AS INT
    INCREMENT BY 1
    MINVALUE 1
    START WITH 1
    NO CYCLE;

-- Create the table
CREATE TABLE recipe (
    -- Fields
    recipe_id INTEGER NOT NULL DEFAULT nextval('seq_recipe_recipe_id'),
    user_id INTEGER NOT NULL,
    recipe_name VARCHAR(100) NOT NULL,
    servings_per_recipe NUMERIC(6, 2) NOT NULL DEFAULT 1,
    serving_label VARCHAR(30) NOT NULL DEFAULT 'serving',
    instructions TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    CONSTRAINT pk_recipe_recipe_id PRIMARY KEY (recipe_id),
    CONSTRAINT fk_recipe_user_id FOREIGN KEY (user_id)
        REFERENCES app_user (user_id) ON DELETE CASCADE,
    CONSTRAINT chk_recipe_recipe_name CHECK (LENGTH(TRIM(recipe_name)) > 0),
    CONSTRAINT chk_recipe_servings_per_recipe CHECK (servings_per_recipe > 0),
    CONSTRAINT chk_recipe_serving_label CHECK (LENGTH(TRIM(serving_label)) > 0)
);

ALTER SEQUENCE seq_recipe_recipe_id OWNED BY recipe.recipe_id;

-- Create indexes
CREATE UNIQUE INDEX unq_recipe_user_id_recipe_name ON recipe (user_id, recipe_name)
    WHERE is_active;

CREATE INDEX idx_recipe_user_id ON recipe (user_id);

-- Trigger assignments
CREATE TRIGGER trg_recipe_set_updated_at
    BEFORE UPDATE ON recipe
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_set_updated_at();

-- Give grants
-- None needed: the master role owns the table.
