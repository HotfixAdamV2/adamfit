/*
    Migration: 000020_create_fx_trg_food_validate_category (up)

    What:
        Creates two trigger functions and their triggers:
        - fx_trg_food_validate_category on food: a food's category must be
          shared (user_id NULL) or owned by the food's user.
        - fx_trg_standard_food_validate_category on standard_food: a
          standard food can only use shared categories.

    Why:
        Since 000018, categories can belong to a user. A foreign key only
        checks that the category exists, not who owns it, so without these
        checks a food could point at another user's private category.

    Notes:
        - Both raise SQLSTATE 23503 (foreign_key_violation) with the name
          of the matching foreign key (fk_food_category_id or
          fk_standard_food_category_id), so the app can treat it like an
          invalid category.
        - fx_trg_copy_standard_foods (000012) still works: it copies
          standard_food.category_id, which this migration guarantees is
          shared, so every copied food passes the food check.
        - The triggers fire only on INSERT or when category_id (or the
          food's user_id) changes, so other edits are not slowed down.
        - A food may still point at an inactive category; the app should
          offer only active categories in its pickers.
*/

-- Trigger function for food
CREATE FUNCTION fx_trg_food_validate_category()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    category_user_id INTEGER;
BEGIN
    SELECT
        user_id
    INTO category_user_id
    FROM food_category
    WHERE category_id = NEW.category_id;

    -- A missing category is left to fk_food_category_id
    IF FOUND AND category_user_id IS NOT NULL AND category_user_id <> NEW.user_id THEN
        RAISE EXCEPTION 'The food category belongs to another user.'
            USING ERRCODE = 'foreign_key_violation',
                CONSTRAINT = 'fk_food_category_id';
    END IF;

    RETURN NEW;
END;
$$;

-- Trigger function for standard_food
CREATE FUNCTION fx_trg_standard_food_validate_category()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    category_user_id INTEGER;
BEGIN
    SELECT
        user_id
    INTO category_user_id
    FROM food_category
    WHERE category_id = NEW.category_id;

    -- A missing category is left to fk_standard_food_category_id
    IF FOUND AND category_user_id IS NOT NULL THEN
        RAISE EXCEPTION 'Standard foods can only use built-in (shared) categories.'
            USING ERRCODE = 'foreign_key_violation',
                CONSTRAINT = 'fk_standard_food_category_id';
    END IF;

    RETURN NEW;
END;
$$;

-- Trigger assignments
CREATE TRIGGER trg_food_validate_category
    BEFORE INSERT OR UPDATE OF category_id, user_id ON food
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_food_validate_category();

CREATE TRIGGER trg_standard_food_validate_category
    BEFORE INSERT OR UPDATE OF category_id ON standard_food
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_standard_food_validate_category();
