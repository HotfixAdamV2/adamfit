"""Queries for the food_log table (the daily nutrition log)."""

from datetime import date

import pandas as pd
from psycopg import errors

from adamfit.db import fetch_all, get_connection
from adamfit.nutrition import MACROS


def get_log(user_id: int, log_date: date) -> pd.DataFrame:
    """
    Load everything a user logged on one day, with per-serving macros.

    Food entries use the food's serving. Recipe entries use one recipe
    serving (``serving_size`` 1, ``serving_unit`` the recipe's serving label).

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
        ``servings``, ``serving_size``, ``serving_unit`` and the per-serving
        macro columns, in the order they were logged.
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
            COALESCE(f.calories, r.calories) AS calories,
            COALESCE(f.protein_g, r.protein_g) AS protein_g,
            COALESCE(f.carbs_g, r.carbs_g) AS carbs_g,
            COALESCE(f.fat_g, r.fat_g) AS fat_g,
            COALESCE(f.fiber_g, r.fiber_g) AS fiber_g
        FROM food_log AS fl
        LEFT JOIN food AS f
            ON f.food_id = fl.food_id
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
        *MACROS,
    ]
    df = pd.DataFrame(rows, columns=columns).set_index("food_log_id")
    numeric = ["servings", "serving_size", *MACROS]
    df[numeric] = df[numeric].astype(float)
    return df


def save_log_changes(
    user_id: int,
    log_date: date,
    adds: list[dict],
    updates: dict[int, float],
    deletes: list[int],
) -> None:
    """
    Add, change and remove a day's log entries in a single transaction.

    Either every change is saved or none are.

    Parameters
    ----------
    user_id : int
        The user who owns the log.
    log_date : date
        The day new entries are logged on.
    adds : list[dict]
        New entries, in the order they were added. Each has ``servings``
        and exactly one of ``food_id`` or ``recipe_id`` (the other is None).
    updates : dict[int, float]
        New number of servings, keyed by ``food_log_id``.
    deletes : list[int]
        Ids of the entries to remove.

    Raises
    ------
    ValueError
        If a number of servings is too large to store. The message is
        written for the user.
    """
    try:
        with get_connection() as conn:
            for food_log_id in deletes:
                conn.execute(
                    """
                    DELETE FROM food_log
                    WHERE food_log_id = %s
                        AND user_id = %s
                    """,
                    (food_log_id, user_id),
                )
            for food_log_id, servings in updates.items():
                conn.execute(
                    """
                    UPDATE food_log
                    SET servings = %s
                    WHERE food_log_id = %s
                        AND user_id = %s
                    """,
                    (servings, food_log_id, user_id),
                )
            for entry in adds:
                conn.execute(
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
                    (user_id, log_date, entry["food_id"], entry["recipe_id"], entry["servings"]),
                )
    except errors.NumericValueOutOfRange:
        raise ValueError("One of the servings is too large.")


def get_daily_totals(user_id: int, start: date | None, end: date) -> pd.DataFrame:
    """
    Add up each day's macros, one row per day that has something logged.

    Food and recipe entries are both included: each entry's per-serving
    macros are multiplied by the servings eaten, then summed per day. Days
    with nothing logged have no row at all (they are not returned as zero).

    Parameters
    ----------
    user_id : int
        The user whose log to add up.
    start : date | None
        First day to include. None includes everything up to ``end``.
    end : date
        Last day to include.

    Returns
    -------
    pd.DataFrame
        Columns ``log_date`` (datetime) and the macro columns in ``MACROS``
        (daily totals as floats), oldest day first. Empty if nothing was
        logged in the range.
    """
    rows = fetch_all(
        """
        SELECT
            fl.log_date,
            SUM(fl.servings * COALESCE(f.calories, r.calories)) AS calories,
            SUM(fl.servings * COALESCE(f.protein_g, r.protein_g)) AS protein_g,
            SUM(fl.servings * COALESCE(f.carbs_g, r.carbs_g)) AS carbs_g,
            SUM(fl.servings * COALESCE(f.fat_g, r.fat_g)) AS fat_g,
            SUM(fl.servings * COALESCE(f.fiber_g, r.fiber_g)) AS fiber_g
        FROM food_log AS fl
        LEFT JOIN food AS f
            ON f.food_id = fl.food_id
        LEFT JOIN vw_recipe_nutrition AS r
            ON r.recipe_id = fl.recipe_id
        WHERE fl.user_id = %s
            AND fl.log_date >= %s
            AND fl.log_date <= %s
        GROUP BY fl.log_date
        ORDER BY fl.log_date
        """,
        # date.min (year 1) stands for "no start date"
        (user_id, start or date.min, end),
    )
    df = pd.DataFrame(rows, columns=["log_date", *MACROS])
    df["log_date"] = pd.to_datetime(df["log_date"])
    # A macro with no values that day (e.g. no fiber recorded) adds up to NULL
    df[list(MACROS)] = df[list(MACROS)].astype(float).fillna(0.0)
    return df
