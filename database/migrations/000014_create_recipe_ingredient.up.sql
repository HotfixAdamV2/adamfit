/*
    Migration: 000014_create_recipe_ingredient (up)

    What:
        Creates the recipe_ingredient table: which foods go into a recipe,
        and how much of each.

    Why:
        A recipe's macros are calculated from its ingredients rather than
        typed in, so changing an ingredient amount updates the recipe.

    Notes:
        - servings is the number of the food's own servings, e.g. 2.27 x
          100 g of chicken breast.
        - Ingredients are removed with their recipe or their food. The app
          only soft-deletes foods, so in practice a food is only really
          deleted when its whole user is. Without the food cascade, deleting
          a user fails: the user -> food cascade can run before the
          user -> recipe -> recipe_ingredient cascade has cleared the rows.
*/

-- Create sequence
CREATE SEQUENCE seq_recipe_ingredient_recipe_ingredient_id AS INT
    INCREMENT BY 1
    MINVALUE 1
    START WITH 1
    NO CYCLE;

-- Create the table
CREATE TABLE recipe_ingredient (
    -- Fields
    recipe_ingredient_id INTEGER NOT NULL DEFAULT nextval('seq_recipe_ingredient_recipe_ingredient_id'),
    recipe_id INTEGER NOT NULL,
    food_id INTEGER NOT NULL,
    servings NUMERIC(8, 3) NOT NULL,
    sort_order SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    CONSTRAINT pk_recipe_ingredient_recipe_ingredient_id PRIMARY KEY (recipe_ingredient_id),
    CONSTRAINT fk_recipe_ingredient_recipe_id FOREIGN KEY (recipe_id)
        REFERENCES recipe (recipe_id) ON DELETE CASCADE,
    CONSTRAINT fk_recipe_ingredient_food_id FOREIGN KEY (food_id)
        REFERENCES food (food_id) ON DELETE CASCADE,
    CONSTRAINT chk_recipe_ingredient_servings CHECK (servings > 0)
);

ALTER SEQUENCE seq_recipe_ingredient_recipe_ingredient_id
    OWNED BY recipe_ingredient.recipe_ingredient_id;

-- Create indexes
CREATE INDEX idx_recipe_ingredient_recipe_id ON recipe_ingredient (recipe_id);

CREATE INDEX idx_recipe_ingredient_food_id ON recipe_ingredient (food_id);

-- Trigger assignments
CREATE TRIGGER trg_recipe_ingredient_set_updated_at
    BEFORE UPDATE ON recipe_ingredient
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_set_updated_at();

-- Give grants
-- None needed: the master role owns the table.
