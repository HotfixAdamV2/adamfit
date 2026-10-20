/*
    Migration: 000021_alter_food_category_unique_include_inactive (down)

    What:
        Rebuilds unq_food_category_user_id_parent_category_id_category_name
        as the partial index from 000018 (WHERE is_active).

    Why:
        Reverts 000021_alter_food_category_unique_include_inactive.

    Notes:
        - Always safe: the partial index is less strict, so every row that
          satisfied the full index also satisfies it.
        - After this, the app's INSERT ... ON CONFLICT (user_id,
          parent_category_id, LOWER(category_name)) fails with 42P10
          (no matching unique index), because ON CONFLICT cannot infer a
          partial index unless the WHERE is repeated.
*/

SET lock_timeout = '5s';

DROP INDEX unq_food_category_user_id_parent_category_id_category_name;

-- Create indexes
CREATE UNIQUE INDEX unq_food_category_user_id_parent_category_id_category_name
    ON food_category (user_id, parent_category_id, LOWER(category_name))
    NULLS NOT DISTINCT
    WHERE is_active;
