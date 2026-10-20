/*
    Migration: 000018_alter_food_category_add_user_id (up)

    What:
        Adds user_id, is_active, created_at and updated_at to
        food_category, attaches fx_trg_set_updated_at, and replaces the
        old (parent_category_id, category_name) unique constraint with a
        case-insensitive, per-owner partial unique index.

    Why:
        Users can now create their own food categories. A NULL user_id is
        a shared, built-in category that every user sees. A value is that
        user's own category, which only they see. Like food and recipe,
        deleting a category in the app sets is_active to FALSE.

    Notes:
        - The existing built-in categories keep user_id NULL.
        - ON DELETE CASCADE removes a user's categories with the user.
        - The new unique index is on (user_id, parent_category_id,
          LOWER(category_name)) with NULLS NOT DISTINCT, so:
            * shared rows (user_id NULL) are unique among themselves,
              including top-level rows (parent_category_id NULL);
            * each user's rows are unique among that user's rows;
            * "Rice" and "rice" collide.
          It is partial (WHERE is_active) so a removed category's name can
          be reused. An index is needed because constraints cannot have a
          WHERE clause or an expression.
        - A user category with the same name as a shared one under the
          same parent is rejected by fx_trg_food_category_validate (000019),
          because the index cannot compare rows with different user_id.
        - The other rules (parent ownership, food ownership) are in 000019
          and 000020.
*/

ALTER TABLE food_category
    ADD COLUMN user_id INTEGER,
    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD CONSTRAINT fk_food_category_user_id FOREIGN KEY (user_id)
        REFERENCES app_user (user_id) ON DELETE CASCADE,
    DROP CONSTRAINT unq_food_category_parent_category_id_category_name;

-- Create indexes
CREATE UNIQUE INDEX unq_food_category_user_id_parent_category_id_category_name
    ON food_category (user_id, parent_category_id, LOWER(category_name))
    NULLS NOT DISTINCT
    WHERE is_active;

CREATE INDEX idx_food_category_user_id ON food_category (user_id);

-- Trigger assignments
CREATE TRIGGER trg_food_category_set_updated_at
    BEFORE UPDATE ON food_category
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_set_updated_at();

-- Give grants
-- None needed: the master role owns the table.
