/*
    Migration: 000021_alter_food_category_unique_include_inactive (up)

    What:
        Rebuilds unq_food_category_user_id_parent_category_id_category_name
        on food_category without its WHERE is_active clause. The name,
        columns, LOWER(category_name) expression and NULLS NOT DISTINCT are
        unchanged.

    Why:
        The partial index from 000018 ignored inactive rows, so re-adding a
        removed category inserted a second row. Covering every row means
        there is one row per (owner, parent, lower(name)), active or not,
        and the app can reactivate a removed category with:
            INSERT ... ON CONFLICT (user_id, parent_category_id,
                LOWER(category_name))
            DO UPDATE SET is_active = TRUE WHERE NOT food_category.is_active
        The ON CONFLICT target only infers a non-partial index (or a
        partial one whose WHERE is repeated), so the WHERE had to go.

    Notes:
        - The index name is kept, so the app's error handling (which
          matches on the constraint name, SQLSTATE 23505) still works.
        - Before rebuilding, the script stops with an error if any rows
          would clash (active or inactive, shared or user-owned), listing
          them. Nothing is deleted or renamed automatically. Fix the rows
          by hand, then run "migrate force 20" and "up" again.
        - A user can now no longer insert, rename or move a category onto
          the name of one of their own inactive categories under the same
          parent. That raises 23505 with this index name. Reactivate the
          old row instead.
        - fx_trg_food_category_validate (000019) is unchanged. Its check
          against shared categories still ignores inactive shared rows: a
          retired built-in category is hidden from users, so a user may
          make their own with that name. The index cannot see that clash
          (user_id differs), so the trigger remains the only guard.
*/

SET lock_timeout = '5s';

-- Stop if any rows would break the new, non-partial index
DO $$
DECLARE
    clash_list TEXT;
BEGIN
    SELECT
        STRING_AGG(
            FORMAT(
                'user_id=%s parent_category_id=%s name=%L category_ids=%s',
                COALESCE(user_id::TEXT, 'NULL (shared)'),
                COALESCE(parent_category_id::TEXT, 'NULL (top level)'),
                lower_name,
                category_ids
            ),
            '; '
        )
    INTO clash_list
    FROM (
        SELECT
            user_id,
            parent_category_id,
            LOWER(category_name) AS lower_name,
            STRING_AGG(
                category_id::TEXT || CASE WHEN is_active THEN '' ELSE ' (inactive)' END,
                ', '
                ORDER BY category_id
            ) AS category_ids
        FROM food_category
        GROUP BY
            user_id,
            parent_category_id,
            LOWER(category_name)
        HAVING COUNT(*) > 1
    ) AS clash;

    IF clash_list IS NOT NULL THEN
        RAISE EXCEPTION 'food_category has rows with the same owner, parent and name (any case), so 000021 cannot make the unique index cover inactive rows. Rename or merge them first: %', clash_list;
    END IF;
END;
$$;

DROP INDEX unq_food_category_user_id_parent_category_id_category_name;

-- Create indexes
CREATE UNIQUE INDEX unq_food_category_user_id_parent_category_id_category_name
    ON food_category (user_id, parent_category_id, LOWER(category_name))
    NULLS NOT DISTINCT;
