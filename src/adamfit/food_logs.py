"""Queries for the food_log table (the daily nutrition log)."""

from datetime import date

import pandas as pd

from adamfit.db import execute, fetch_all
from adamfit.nutrition import MACROS


def get_log(user_id: int, log_date: date) -> pd.DataFrame:
    """
    Load everything a user logged on one day, with per-serving macros.

    Food entries use the food's serving. Recipe entries use one recipe
    serving (``serving_size`` 1, ``serving_unit`` the recipe's serving label,
    no ``grams_per_unit``).

    Parameters
    ----------
    user_id : int
        The user whose log to load.
    log_date : date
        The day to load.

    Returns
    -------
    pd.DataFrame
        Indexed by ``food_log_id``, with columns ``item_name``,
        ``servings``, ``serving_size``, ``serving_unit``, ``grams_per_unit``
        and the per-serving macro columns, in the order they were logged.
        This is the shape ``nutrition.scale_entries`` expects.
    """
    rows = fetch_all(
        """
        SELECT
            fl.food_log_id,
            COALESCE(f.food_name, r.recipe_name) AS item_name,
            fl.servings,
            COALESCE(f.serving_size, 1) AS serving_size,
            COALESCE(f.serving_unit, r.serving_label) AS serving_unit,
            su.grams_per_unit,
            COALESCE(f.calories, r.calories) AS calories,
            COALESCE(f.protein_g, r.protein_g) AS protein_g,
            COALESCE(f.carbs_g, r.carbs_g) AS carbs_g,
            COALESCE(f.fat_g, r.fat_g) AS fat_g,
            COALESCE(f.fiber_g, r.fiber_g) AS fiber_g
        FROM food_log AS fl
        LEFT JOIN food AS f
            ON f.food_id = fl.food_id
        LEFT JOIN serving_unit AS su
            ON su.unit_code = f.serving_unit
        LEFT JOIN vw_recipe_nutrition AS r
            ON r.recipe_id = fl.recipe_id
        WHERE fl.user_id = %s
            AND fl.log_date = %s
        ORDER BY
            fl.created_at,
            fl.food_log_id
        """,
        (user_id, log_date),
    )
    columns = [
        "food_log_id",
        "item_name",
        "servings",
        "serving_size",
        "serving_unit",
        "grams_per_unit",
        *MACROS,
    ]
    df = pd.DataFrame(rows, columns=columns).set_index("food_log_id")
    numeric = ["servings", "serving_size", "grams_per_unit", *MACROS]
    df[numeric] = df[numeric].astype(float)
    return df


def add_entry(
    user_id: int,
    log_date: date,
    servings: float,
    food_id: int | None = None,
    recipe_id: int | None = None,
) -> None:
    """
    Log some servings of a food or a recipe. Pass exactly one of the two ids.

    Parameters
    ----------
    user_id : int
        The user who ate it.
    log_date : date
        The day it was eaten.
    servings : float
        Number of the food's (or recipe's) servings.
    food_id : int | None, optional
        The food eaten.
    recipe_id : int | None, optional
        The recipe eaten.
    """
    execute(
        """
        INSERT INTO food_log (
            user_id,
            log_date,
            food_id,
            recipe_id,
            servings
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, log_date, food_id, recipe_id, servings),
    )


def update_entry(user_id: int, food_log_id: int, servings: float) -> None:
    """
    Change the number of servings for a log entry.

    Parameters
    ----------
    user_id : int
        The user who owns the entry.
    food_log_id : int
        The entry to change.
    servings : float
        New number of servings.
    """
    execute(
        """
        UPDATE food_log
        SET servings = %s
        WHERE food_log_id = %s
            AND user_id = %s
        """,
        (servings, food_log_id, user_id),
    )


def delete_entry(user_id: int, food_log_id: int) -> None:
    """
    Remove a log entry.

    Parameters
    ----------
    user_id : int
        The user who owns the entry.
    food_log_id : int
        The entry to remove.
    """
    execute(
        """
        DELETE FROM food_log
        WHERE food_log_id = %s
            AND user_id = %s
        """,
        (food_log_id, user_id),
    )
