/*
    Migration: 000019_create_fx_trg_food_category_validate (up)

    What:
        Creates the trigger function fx_trg_food_category_validate and
        attaches it to food_category (BEFORE INSERT OR UPDATE). It enforces
        the ownership rules for user-created categories that a constraint
        or index cannot express.

    Why:
        000018 lets users own categories. The unique index stops duplicates
        within one owner, but these rules compare rows with different
        owners, or look at other tables, so they need a trigger.

    Notes:
        Every error sets a SQLSTATE and a constraint name, so the app can
        catch it (psycopg: e.sqlstate and e.diag.constraint_name):
        - 23514 check_violation, chk_food_category_user_id:
          user_id can never change (shared <-> user, or user A -> user B).
        - 23503 foreign_key_violation, fk_food_category_parent_category_id:
          the parent must be shared or owned by the same user. A shared
          category can only have a shared parent.
        - 23514 check_violation, chk_food_category_parent_category_id:
          a category cannot be its own parent or ancestor (no loops).
        - 23505 unique_violation,
          unq_food_category_user_id_parent_category_id_category_name:
          an active user category cannot have the same name (any case) as
          an active shared category under the same parent. This is the
          same name the unique index uses for a duplicate of the user's
          own category, so the app can handle both the same way.
        - 2BP01 dependent_objects_still_exist, chk_food_category_is_active:
          a category cannot be soft-deleted (is_active -> FALSE) while
          active foods, standard foods or active sub-categories use it.
        Shared categories are managed by hand, so a new shared category
        that matches an existing user category is not blocked.
*/

-- Trigger function
CREATE FUNCTION fx_trg_food_category_validate()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    parent_found BOOLEAN;
    parent_user_id INTEGER;
BEGIN
    -- The owner of a category never changes
    IF TG_OP = 'UPDATE' AND NEW.user_id IS DISTINCT FROM OLD.user_id THEN
        RAISE EXCEPTION 'The owner of a food category cannot be changed.'
            USING ERRCODE = 'check_violation',
                CONSTRAINT = 'chk_food_category_user_id';
    END IF;

    -- Parent checks, only when the parent is set or changes
    IF NEW.parent_category_id IS NOT NULL
        AND (TG_OP = 'INSERT' OR NEW.parent_category_id IS DISTINCT FROM OLD.parent_category_id)
    THEN
        SELECT
            user_id
        INTO parent_user_id
        FROM food_category
        WHERE category_id = NEW.parent_category_id;

        parent_found := FOUND;

        -- A missing parent is left to fk_food_category_parent_category_id
        IF parent_found AND parent_user_id IS NOT NULL AND NEW.user_id IS NULL THEN
            RAISE EXCEPTION 'A shared food category cannot be placed under a user''s own category.'
                USING ERRCODE = 'foreign_key_violation',
                    CONSTRAINT = 'fk_food_category_parent_category_id';
        END IF;

        IF parent_found AND parent_user_id IS NOT NULL AND parent_user_id <> NEW.user_id THEN
            RAISE EXCEPTION 'The parent category belongs to another user.'
                USING ERRCODE = 'foreign_key_violation',
                    CONSTRAINT = 'fk_food_category_parent_category_id';
        END IF;

        -- No loops: walk up from the new parent and look for this row
        IF NEW.parent_category_id = NEW.category_id
            OR EXISTS (
                WITH RECURSIVE
                    ancestor AS (
                        SELECT
                            category_id,
                            parent_category_id
                        FROM food_category
                        WHERE category_id = NEW.parent_category_id
                        UNION
                        SELECT
                            fc.category_id,
                            fc.parent_category_id
                        FROM food_category AS fc
                        INNER JOIN ancestor AS a
                            ON fc.category_id = a.parent_category_id
                    )
                SELECT
                    1
                FROM ancestor
                WHERE category_id = NEW.category_id
            )
        THEN
            RAISE EXCEPTION 'A food category cannot be its own parent or ancestor.'
                USING ERRCODE = 'check_violation',
                    CONSTRAINT = 'chk_food_category_parent_category_id';
        END IF;
    END IF;

    -- A user category cannot duplicate an active shared one under the same parent
    IF NEW.user_id IS NOT NULL
        AND NEW.is_active
        AND (
            TG_OP = 'INSERT'
            OR NEW.category_name IS DISTINCT FROM OLD.category_name
            OR NEW.parent_category_id IS DISTINCT FROM OLD.parent_category_id
            OR NOT OLD.is_active
        )
        AND EXISTS (
            SELECT
                1
            FROM food_category
            WHERE user_id IS NULL
                AND is_active
                AND parent_category_id IS NOT DISTINCT FROM NEW.parent_category_id
                AND LOWER(category_name) = LOWER(NEW.category_name)
        )
    THEN
        RAISE EXCEPTION 'A built-in category named "%" already exists here.', NEW.category_name
            USING ERRCODE = 'unique_violation',
                CONSTRAINT = 'unq_food_category_user_id_parent_category_id_category_name';
    END IF;

    -- Block soft-deleting a category that is still in use
    IF TG_OP = 'UPDATE' AND OLD.is_active AND NOT NEW.is_active THEN
        IF EXISTS (
            SELECT
                1
            FROM food
            WHERE category_id = NEW.category_id
                AND is_active
        ) THEN
            RAISE EXCEPTION 'The category "%" still has active foods. Move or remove them first.', NEW.category_name
                USING ERRCODE = 'dependent_objects_still_exist',
                    CONSTRAINT = 'chk_food_category_is_active';
        END IF;

        IF EXISTS (
            SELECT
                1
            FROM standard_food
            WHERE category_id = NEW.category_id
        ) THEN
            RAISE EXCEPTION 'The category "%" is used by standard foods.', NEW.category_name
                USING ERRCODE = 'dependent_objects_still_exist',
                    CONSTRAINT = 'chk_food_category_is_active';
        END IF;

        IF EXISTS (
            SELECT
                1
            FROM food_category
            WHERE parent_category_id = NEW.category_id
                AND is_active
        ) THEN
            RAISE EXCEPTION 'The category "%" still has active sub-categories. Remove them first.', NEW.category_name
                USING ERRCODE = 'dependent_objects_still_exist',
                    CONSTRAINT = 'chk_food_category_is_active';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

-- Trigger assignments
CREATE TRIGGER trg_food_category_validate
    BEFORE INSERT OR UPDATE ON food_category
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_food_category_validate();
