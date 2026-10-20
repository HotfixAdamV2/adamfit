/*
    Migration: 000018_alter_food_category_add_user_id (down)

    What:
        Removes every user-owned food category, drops user_id, is_active,
        created_at, updated_at, their index and trigger, and restores the
        unq_food_category_parent_category_id_category_name constraint.

    Why:
        Reverts 000018_alter_food_category_add_user_id.

    Notes:
        - Before 000018 every category was shared, so user-owned
          categories cannot be kept: turning them into shared rows would
          show one user's private categories to everyone and could clash
          with the restored unique constraint. They are deleted.
        - Foods are never deleted (recipes and the food log use them).
          Every food (active or not) in a user category is first moved to
          that category's nearest shared ancestor, e.g. a food in the
          user's "Protein > Shakes" moves to the shared "Protein". That
          ancestor may be a top-level category.
        - If a food is in a user category with no shared ancestor (a
          user-owned top-level category tree), there is nowhere safe to
          move it, so this script stops with an error and changes nothing.
          Move those foods to a shared category by hand, then run
          "migrate force 18" (golang-migrate marks the failed run dirty)
          and "down 1" again.
        - Shared rows that were soft-deleted become visible again, because
          is_active is dropped. If one has the same parent and exact name
          as another shared row, restoring the constraint fails and
          nothing changes. Remove or rename the duplicate first.
        - 000020 and 000019 must be rolled back first (golang-migrate does
          this in order), since their triggers use the columns dropped here.
*/

-- Stop if any food sits in a user category tree with no shared ancestor
DO $$
DECLARE
    stranded_count INTEGER;
BEGIN
    WITH RECURSIVE
        walk AS (
            SELECT
                category_id AS start_id,
                parent_category_id AS next_id
            FROM food_category
            WHERE user_id IS NOT NULL
            UNION
            SELECT
                w.start_id,
                fc.parent_category_id
            FROM walk AS w
            INNER JOIN food_category AS fc
                ON fc.category_id = w.next_id
            WHERE fc.user_id IS NOT NULL
        ),
        shared_ancestor AS (
            SELECT
                w.start_id,
                w.next_id AS shared_category_id
            FROM walk AS w
            INNER JOIN food_category AS fc
                ON fc.category_id = w.next_id
            WHERE fc.user_id IS NULL
        )
    SELECT
        COUNT(*)
    INTO stranded_count
    FROM food AS f
    INNER JOIN food_category AS fc
        ON fc.category_id = f.category_id
    LEFT JOIN shared_ancestor AS sa
        ON sa.start_id = f.category_id
    WHERE fc.user_id IS NOT NULL
        AND sa.shared_category_id IS NULL;

    IF stranded_count > 0 THEN
        RAISE EXCEPTION '% food(s) are in user-owned categories with no shared parent. Move them to a shared category before rolling back 000018.', stranded_count;
    END IF;
END;
$$;

-- Move foods in user categories to the nearest shared ancestor
WITH RECURSIVE
    walk AS (
        SELECT
            category_id AS start_id,
            parent_category_id AS next_id
        FROM food_category
        WHERE user_id IS NOT NULL
        UNION
        SELECT
            w.start_id,
            fc.parent_category_id
        FROM walk AS w
        INNER JOIN food_category AS fc
            ON fc.category_id = w.next_id
        WHERE fc.user_id IS NOT NULL
    ),
    shared_ancestor AS (
        SELECT
            w.start_id,
            w.next_id AS shared_category_id
        FROM walk AS w
        INNER JOIN food_category AS fc
            ON fc.category_id = w.next_id
        WHERE fc.user_id IS NULL
    )
UPDATE food AS f
SET category_id = sa.shared_category_id
FROM shared_ancestor AS sa
WHERE f.category_id = sa.start_id;

-- Delete every user category (children and parents in one statement,
-- so the self-referencing foreign key is checked once at the end)
DELETE FROM food_category
WHERE user_id IS NOT NULL;

DROP TRIGGER trg_food_category_set_updated_at ON food_category;

DROP INDEX idx_food_category_user_id;

DROP INDEX unq_food_category_user_id_parent_category_id_category_name;

ALTER TABLE food_category
    DROP CONSTRAINT fk_food_category_user_id,
    DROP COLUMN user_id,
    DROP COLUMN is_active,
    DROP COLUMN created_at,
    DROP COLUMN updated_at,
    ADD CONSTRAINT unq_food_category_parent_category_id_category_name
        UNIQUE NULLS NOT DISTINCT (parent_category_id, category_name);
