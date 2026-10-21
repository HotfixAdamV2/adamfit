/*
    Migration: 000017_alter_food_category_drop_sort_order (up)

    What:
        Drops the sort_order column from the food_category table.

    Why:
        The app now orders categories and sub-categories alphabetically by
        category_name (see src/adamfit/foods.py), so a hand-maintained sort
        order is no longer needed.

    Notes:
        - Nothing else depends on this column: no index, constraint, view,
          function or trigger uses it. Its default and NOT NULL constraint
          are dropped with it.
        - serving_unit.sort_order and recipe_ingredient.sort_order are
          different columns and are not touched.
*/

ALTER TABLE food_category
    DROP COLUMN sort_order;
