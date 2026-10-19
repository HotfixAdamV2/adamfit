"""Queries for the food, food_category and serving_unit tables."""

import pandas as pd
import streamlit as st
from psycopg import errors

from adamfit.db import fetch_all, get_connection
from adamfit.nutrition import MACROS

# Editable columns of a food, in table order
FOOD_FIELDS = ["food_name", "category_id", "serving_size", "serving_unit", *MACROS]


@st.cache_data(ttl=3600)
def get_serving_units() -> pd.DataFrame:
    """
    Load every unit a food's serving can be measured in.

    Units rarely change, so the result is cached for an hour. Restart the app
    (or wait) after adding one to the serving_unit table.

    Returns
    -------
    pd.DataFrame
        Indexed by ``unit_code`` (e.g. ``"oz"``), with columns ``unit_name``
        and ``unit_type``, in display order.
    """
    rows = fetch_all(
        """
        SELECT
            unit_code,
            unit_name,
            unit_type
        FROM serving_unit
        ORDER BY sort_order
        """
    )
    df = pd.DataFrame(rows, columns=["unit_code", "unit_name", "unit_type"])
    return df.set_index("unit_code")


@st.cache_data(ttl=3600)
def get_categories() -> pd.DataFrame:
    """
    Load every sub-category with its parent category's name.

    Categories rarely change, so the result is cached for an hour.

    Returns
    -------
    pd.DataFrame
        Columns ``category_id``, ``parent_name`` and ``label`` (e.g.
        ``"Protein › Poultry"``), in display order.
    """
    rows = fetch_all(
        """
        SELECT
            fc.category_id,
            parent.category_name AS parent_name,
            parent.category_name || ' › ' || fc.category_name AS label
        FROM food_category AS fc
        INNER JOIN food_category AS parent
            ON parent.category_id = fc.parent_category_id
        ORDER BY
            parent.category_name,
            fc.category_name
        """
    )
    return pd.DataFrame(rows, columns=["category_id", "parent_name", "label"])


def get_foods(user_id: int) -> pd.DataFrame:
    """
    Load a user's active foods, grouped by category.

    Parameters
    ----------
    user_id : int
        The user whose foods to load.

    Returns
    -------
    pd.DataFrame
        Indexed by ``food_id``, with columns ``food_name``, ``category_id``,
        ``parent_name``, ``sub_category_name``, ``category_label``, ``serving_size``,
        ``serving_unit`` and the macro columns (per serving, as floats).
    """
    rows = fetch_all(
        """
        SELECT
            f.food_id,
            f.food_name,
            f.category_id,
            parent.category_name AS parent_name,
            fc.category_name AS sub_category_name,
            parent.category_name || ' › ' || fc.category_name AS category_label,
            f.serving_size,
            f.serving_unit,
            f.calories,
            f.protein_g,
            f.carbs_g,
            f.fat_g,
            f.fiber_g
        FROM food AS f
        INNER JOIN food_category AS fc
            ON fc.category_id = f.category_id
        INNER JOIN food_category AS parent
            ON parent.category_id = fc.parent_category_id
        WHERE f.user_id = %s
            AND f.is_active
        ORDER BY
            parent.category_name,
            fc.category_name,
            f.food_name
        """,
        (user_id,),
    )
    columns = [
        "food_id",
        "food_name",
        "category_id",
        "parent_name",
        "sub_category_name",
        "category_label",
        "serving_size",
        "serving_unit",
        *MACROS,
    ]
    df = pd.DataFrame(rows, columns=columns).set_index("food_id")
    numeric = ["serving_size", *MACROS]
    df[numeric] = df[numeric].astype(float)
    return df


def _clean_food(values: dict) -> dict:
    """
    Check a food's values and fill in defaults before saving.

    Parameters
    ----------
    values : dict
        Values keyed by the names in ``FOOD_FIELDS``. Missing macros count
        as zero.

    Returns
    -------
    dict
        The cleaned values, keyed by ``FOOD_FIELDS``.

    Raises
    ------
    ValueError
        If a required value is missing or out of range. The message is
        written for the user.
    """
    name = (values.get("food_name") or "").strip()
    if not name:
        raise ValueError("Every food needs a name.")
    if values.get("category_id") is None:
        raise ValueError(f"Choose a category for {name}.")
    serving_size = values.get("serving_size")
    if serving_size is None or pd.isna(serving_size) or serving_size <= 0:
        raise ValueError(f"The serving size for {name} must be more than zero.")
    if values.get("serving_unit") not in get_serving_units().index:
        raise ValueError(f"Choose a serving unit for {name}.")

    cleaned = {
        "food_name": name,
        "category_id": int(values["category_id"]),
        "serving_size": float(serving_size),
        "serving_unit": values["serving_unit"],
    }
    for column, label in MACROS.items():
        value = values.get(column)
        value = 0.0 if value is None or pd.isna(value) else float(value)
        if value < 0:
            raise ValueError(f"{label} for {name} can't be negative.")
        cleaned[column] = value
    return cleaned


def _food_params(values: dict) -> tuple:
    """
    Return a food's values in the column order used by the SQL below.

    The order is written out here rather than taken from ``FOOD_FIELDS``,
    so reordering ``MACROS`` for display can never put a value in the
    wrong column.

    Parameters
    ----------
    values : dict
        Cleaned values from ``_clean_food``.

    Returns
    -------
    tuple
        ``food_name``, ``category_id``, ``serving_size``, ``serving_unit``,
        ``calories``, ``protein_g``, ``carbs_g``, ``fat_g``, ``fiber_g``.
    """
    return (
        values["food_name"],
        values["category_id"],
        values["serving_size"],
        values["serving_unit"],
        values["calories"],
        values["protein_g"],
        values["carbs_g"],
        values["fat_g"],
        values["fiber_g"],
    )


def save_food_changes(
    user_id: int,
    inserts: list[dict],
    updates: dict[int, dict],
    deletes: list[int],
) -> None:
    """
    Add, edit and remove a user's foods in a single transaction.

    Either every change is saved or none are. Removing a food only hides it
    (``is_active = FALSE``), so recipes and log entries that use it still work.

    Parameters
    ----------
    user_id : int
        The user who owns the foods.
    inserts : list[dict]
        New foods, each keyed by the names in ``FOOD_FIELDS``.
    updates : dict[int, dict]
        Full new values for existing foods, keyed by ``food_id``.
    deletes : list[int]
        Ids of foods to remove.

    Raises
    ------
    ValueError
        If any food is invalid or two active foods would share a name. The
        message is written for the user.
    """
    inserts = [_clean_food(values) for values in inserts]
    updates = {food_id: _clean_food(values) for food_id, values in updates.items()}

    try:
        with get_connection() as conn:
            # Remove first, so a removed food's name can be reused right away
            for food_id in deletes:
                conn.execute(
                    """
                    UPDATE food
                    SET is_active = FALSE
                    WHERE food_id = %s
                        AND user_id = %s
                    """,
                    (food_id, user_id),
                )
            for food_id, values in updates.items():
                conn.execute(
                    """
                    UPDATE food
                    SET
                        food_name = %s,
                        category_id = %s,
                        serving_size = %s,
                        serving_unit = %s,
                        calories = %s,
                        protein_g = %s,
                        carbs_g = %s,
                        fat_g = %s,
                        fiber_g = %s
                    WHERE food_id = %s
                        AND user_id = %s
                    """,
                    (*_food_params(values), food_id, user_id),
                )
            for values in inserts:
                conn.execute(
                    """
                    INSERT INTO food (
                        user_id,
                        food_name,
                        category_id,
                        serving_size,
                        serving_unit,
                        calories,
                        protein_g,
                        carbs_g,
                        fat_g,
                        fiber_g
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, *_food_params(values)),
                )
    except errors.UniqueViolation:
        raise ValueError("You already have a food with that name. Food names must be unique.")
    except errors.NumericValueOutOfRange:
        raise ValueError("One of the numbers is too large.")
