"""Queries for the recipe and recipe_ingredient tables.

Recipe macros are never stored. They come from the vw_recipe_nutrition view,
which adds up the ingredients.
"""

import pandas as pd
from psycopg import errors

from adamfit.db import execute, fetch_all, fetch_one
from adamfit.nutrition import MACROS


def get_recipes(user_id: int) -> pd.DataFrame:
    """
    Load a user's active recipes with their per-serving macros.

    Parameters
    ----------
    user_id : int
        The user whose recipes to load.

    Returns
    -------
    pd.DataFrame
        Indexed by ``recipe_id``, with columns ``recipe_name``,
        ``servings_per_recipe``, ``serving_label`` and the macro columns
        (per serving, as floats), sorted by name.
    """
    rows = fetch_all(
        """
        SELECT
            recipe_id,
            recipe_name,
            servings_per_recipe,
            serving_label,
            calories,
            protein_g,
            carbs_g,
            fat_g,
            fiber_g
        FROM vw_recipe_nutrition
        WHERE user_id = %s
            AND is_active
        ORDER BY LOWER(recipe_name)
        """,
        (user_id,),
    )
    columns = ["recipe_id", "recipe_name", "servings_per_recipe", "serving_label", *MACROS]
    df = pd.DataFrame(rows, columns=columns).set_index("recipe_id")
    numeric = ["servings_per_recipe", *MACROS]
    df[numeric] = df[numeric].astype(float)
    return df


def get_recipe(user_id: int, recipe_id: int) -> dict | None:
    """
    Fetch one recipe, including its instructions and macro totals.

    Parameters
    ----------
    user_id : int
        The user who owns the recipe.
    recipe_id : int
        The recipe to fetch.

    Returns
    -------
    dict | None
        Every column of vw_recipe_nutrition plus ``instructions``, or None
        if the recipe does not exist, is not this user's, or was removed.
    """
    return fetch_one(
        """
        SELECT
            v.*,
            r.instructions
        FROM vw_recipe_nutrition AS v
        INNER JOIN recipe AS r
            ON r.recipe_id = v.recipe_id
        WHERE v.recipe_id = %s
            AND v.user_id = %s
            AND v.is_active
        """,
        (recipe_id, user_id),
    )


def create_recipe(
    user_id: int,
    recipe_name: str,
    servings_per_recipe: float,
    serving_label: str,
) -> int:
    """
    Create an empty recipe and return its id.

    Parameters
    ----------
    user_id : int
        The user who will own the recipe.
    recipe_name : str
        Name of the recipe, e.g. ``"Chicken and rice"``.
    servings_per_recipe : float
        How many servings the whole recipe makes.
    serving_label : str
        What one serving is called, e.g. ``"bowl"``.

    Returns
    -------
    int
        The new recipe's id.

    Raises
    ------
    ValueError
        If the user already has an active recipe with that name.
    """
    try:
        row = fetch_one(
            """
            INSERT INTO recipe (
                user_id,
                recipe_name,
                servings_per_recipe,
                serving_label
            )
            VALUES (%s, %s, %s, %s)
            RETURNING recipe_id
            """,
            (user_id, recipe_name.strip(), servings_per_recipe, serving_label.strip()),
        )
    except errors.UniqueViolation:
        raise ValueError(f"You already have a recipe called {recipe_name.strip()}.")
    return row["recipe_id"]


def update_recipe(
    user_id: int,
    recipe_id: int,
    recipe_name: str,
    servings_per_recipe: float,
    serving_label: str,
    instructions: str | None,
) -> None:
    """
    Save a recipe's name, yield and instructions.

    Parameters
    ----------
    user_id : int
        The user who owns the recipe.
    recipe_id : int
        The recipe to update.
    recipe_name : str
        New name.
    servings_per_recipe : float
        How many servings the whole recipe makes.
    serving_label : str
        What one serving is called, e.g. ``"bowl"``.
    instructions : str | None
        Cooking instructions (Markdown), or None for none.

    Raises
    ------
    ValueError
        If the user already has another active recipe with that name.
    """
    try:
        execute(
            """
            UPDATE recipe
            SET
                recipe_name = %s,
                servings_per_recipe = %s,
                serving_label = %s,
                instructions = %s
            WHERE recipe_id = %s
                AND user_id = %s
            """,
            (
                recipe_name.strip(),
                servings_per_recipe,
                serving_label.strip(),
                (instructions or "").strip() or None,
                recipe_id,
                user_id,
            ),
        )
    except errors.UniqueViolation:
        raise ValueError(f"You already have a recipe called {recipe_name.strip()}.")


def delete_recipe(user_id: int, recipe_id: int) -> None:
    """
    Remove a recipe from the user's list.

    The row is kept (``is_active = FALSE``) so past log entries still show
    its macros.

    Parameters
    ----------
    user_id : int
        The user who owns the recipe.
    recipe_id : int
        The recipe to remove.
    """
    execute(
        """
        UPDATE recipe
        SET is_active = FALSE
        WHERE recipe_id = %s
            AND user_id = %s
        """,
        (recipe_id, user_id),
    )


def get_ingredients(user_id: int, recipe_id: int) -> pd.DataFrame:
    """
    Load a recipe's ingredients with each food's serving and macros.

    Parameters
    ----------
    user_id : int
        The user who owns the recipe.
    recipe_id : int
        The recipe whose ingredients to load.

    Returns
    -------
    pd.DataFrame
        Indexed by ``recipe_ingredient_id``, with columns ``item_name``,
        ``servings``, ``serving_size``, ``serving_unit``, ``grams_per_unit``
        and the food's per-serving macro columns, in the order they were
        added. This is the shape ``nutrition.scale_entries`` expects.
    """
    rows = fetch_all(
        """
        SELECT
            ri.recipe_ingredient_id,
            f.food_name AS item_name,
            ri.servings,
            f.serving_size,
            f.serving_unit,
            su.grams_per_unit,
            f.calories,
            f.protein_g,
            f.carbs_g,
            f.fat_g,
            f.fiber_g
        FROM recipe_ingredient AS ri
        INNER JOIN recipe AS r
            ON r.recipe_id = ri.recipe_id
        INNER JOIN food AS f
            ON f.food_id = ri.food_id
        INNER JOIN serving_unit AS su
            ON su.unit_code = f.serving_unit
        WHERE ri.recipe_id = %s
            AND r.user_id = %s
        ORDER BY
            ri.sort_order,
            ri.recipe_ingredient_id
        """,
        (recipe_id, user_id),
    )
    columns = [
        "recipe_ingredient_id",
        "item_name",
        "servings",
        "serving_size",
        "serving_unit",
        "grams_per_unit",
        *MACROS,
    ]
    df = pd.DataFrame(rows, columns=columns).set_index("recipe_ingredient_id")
    numeric = ["servings", "serving_size", "grams_per_unit", *MACROS]
    df[numeric] = df[numeric].astype(float)
    return df


def add_ingredient(user_id: int, recipe_id: int, food_id: int, servings: float) -> None:
    """
    Add a food to the end of a recipe's ingredient list.

    Nothing is added unless both the recipe and the food belong to the user.

    Parameters
    ----------
    user_id : int
        The user who owns the recipe and the food.
    recipe_id : int
        The recipe to add to.
    food_id : int
        The food to add.
    servings : float
        How many of the food's servings go into the recipe.
    """
    execute(
        """
        INSERT INTO recipe_ingredient (
            recipe_id,
            food_id,
            servings,
            sort_order
        )
        SELECT
            r.recipe_id,
            f.food_id,
            %s,
            COALESCE(
                (
                    SELECT MAX(sort_order) + 1
                    FROM recipe_ingredient
                    WHERE recipe_id = r.recipe_id
                ),
                0
            )
        FROM recipe AS r
        INNER JOIN food AS f
            ON f.user_id = r.user_id
        WHERE r.recipe_id = %s
            AND f.food_id = %s
            AND r.user_id = %s
        """,
        (servings, recipe_id, food_id, user_id),
    )


def update_ingredient(user_id: int, recipe_ingredient_id: int, servings: float) -> None:
    """
    Change how much of a food goes into a recipe.

    Parameters
    ----------
    user_id : int
        The user who owns the recipe.
    recipe_ingredient_id : int
        The ingredient row to change.
    servings : float
        New number of the food's servings.
    """
    execute(
        """
        UPDATE recipe_ingredient AS ri
        SET servings = %s
        FROM recipe AS r
        WHERE r.recipe_id = ri.recipe_id
            AND ri.recipe_ingredient_id = %s
            AND r.user_id = %s
        """,
        (servings, recipe_ingredient_id, user_id),
    )


def delete_ingredient(user_id: int, recipe_ingredient_id: int) -> None:
    """
    Remove a food from a recipe.

    Parameters
    ----------
    user_id : int
        The user who owns the recipe.
    recipe_ingredient_id : int
        The ingredient row to remove.
    """
    execute(
        """
        DELETE FROM recipe_ingredient AS ri
        USING recipe AS r
        WHERE r.recipe_id = ri.recipe_id
            AND ri.recipe_ingredient_id = %s
            AND r.user_id = %s
        """,
        (recipe_ingredient_id, user_id),
    )
