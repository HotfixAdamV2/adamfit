/*
    Migration: 000006_create_food_category (up)

    What:
        Creates the food_category table: a two-level list of categories
        (e.g. Protein) and sub-categories (e.g. Poultry) for foods.

    Why:
        Nutrition tracking groups foods so the food list can be filtered
        and browsed. Categories are shared by every user and are not
        user-editable.

    Notes:
        - A row with parent_category_id NULL is a top-level category. A row
          with a parent is a sub-category. Foods always point at a
          sub-category.
        - NULLS NOT DISTINCT makes two top-level categories with the same
          name collide, which a plain UNIQUE would allow.
*/

-- Create sequence
CREATE SEQUENCE seq_food_category_category_id AS INT
    INCREMENT BY 1
    MINVALUE 1
    START WITH 1
    NO CYCLE;

-- Create the table
CREATE TABLE food_category (
    -- Fields
    category_id INTEGER NOT NULL DEFAULT nextval('seq_food_category_category_id'),
    category_name VARCHAR(50) NOT NULL,
    parent_category_id INTEGER,
    sort_order SMALLINT NOT NULL DEFAULT 0,
    -- Constraints
    CONSTRAINT pk_food_category_category_id PRIMARY KEY (category_id),
    CONSTRAINT fk_food_category_parent_category_id FOREIGN KEY (parent_category_id)
        REFERENCES food_category (category_id),
    CONSTRAINT unq_food_category_parent_category_id_category_name
        UNIQUE NULLS NOT DISTINCT (parent_category_id, category_name)
);

ALTER SEQUENCE seq_food_category_category_id OWNED BY food_category.category_id;

-- Give grants
-- None needed: the master role owns the table.
