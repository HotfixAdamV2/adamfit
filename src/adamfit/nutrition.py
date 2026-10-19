"""Shared nutrition maths: servings, amounts and macro totals.

Every food has one fixed serving (e.g. 4 oz, or 1 tbsp) and its macros are
for that serving. Recipes and log entries store a number of servings. These
helpers turn servings into the amount a person actually ate (e.g. 8 oz) and
back, and scale the macros to match.

Weights are shown in the user's preferred unit: ounces for imperial, grams
for metric. A food's serving unit is a weight when the serving_unit table
gives it a ``grams_per_unit`` (g and oz today). Every other unit (tbsp,
piece, bar, ...) is shown as is.

Recipes are treated as a food whose serving is "1 <serving label>", with no
``grams_per_unit``.
"""

import pandas as pd

from adamfit.units import GRAMS_PER_OZ

# Macro columns, in display order, with their labels
MACROS = {
    "calories": "Calories",
    "protein_g": "Protein (g)",
    "carbs_g": "Carbs (g)",
    "fat_g": "Fat (g)",
    "fiber_g": "Fiber (g)",
}


def _is_weight(grams_per_unit: float | None) -> bool:
    """
    Return True if a serving unit is a weight.

    Parameters
    ----------
    grams_per_unit : float | None
        The unit's grams per unit from the serving_unit table. None (or NaN,
        as pandas stores missing numbers) for units that are not weights.

    Returns
    -------
    bool
        True for weight units such as g and oz.
    """
    return grams_per_unit is not None and not pd.isna(grams_per_unit)


def _display_weight(unit_system: str) -> tuple[str, float]:
    """
    Return the weight unit a user prefers, and how many grams are in one.

    Parameters
    ----------
    unit_system : str
        Either ``"imperial"`` or ``"metric"``.

    Returns
    -------
    tuple[str, float]
        ``("oz", 28.35...)`` for imperial, ``("g", 1.0)`` for metric.
    """
    return ("oz", GRAMS_PER_OZ) if unit_system == "imperial" else ("g", 1.0)


def amount_unit(serving_unit: str, grams_per_unit: float | None, unit_system: str) -> str:
    """
    Return the unit a user enters and sees amounts in.

    Parameters
    ----------
    serving_unit : str
        The food's serving unit, e.g. ``"g"``, ``"oz"`` or ``"tbsp"``.
    grams_per_unit : float | None
        Grams in one ``serving_unit``, or None if it is not a weight.
    unit_system : str
        Either ``"imperial"`` or ``"metric"``.

    Returns
    -------
    str
        ``"oz"`` or ``"g"`` for weights, otherwise ``serving_unit``.
    """
    if _is_weight(grams_per_unit):
        return _display_weight(unit_system)[0]
    return serving_unit


def to_amount(
    servings: float,
    serving_size: float,
    grams_per_unit: float | None,
    unit_system: str,
) -> float:
    """
    Convert a number of servings into the amount shown to the user.

    Parameters
    ----------
    servings : float
        Number of servings, as stored in the database.
    serving_size : float
        Size of one serving, in the food's serving unit.
    grams_per_unit : float | None
        Grams in one of the food's serving units, or None if it is not a
        weight.
    unit_system : str
        Either ``"imperial"`` or ``"metric"``.

    Returns
    -------
    float
        The amount in ``amount_unit(...)``.
    """
    amount = servings * serving_size
    if _is_weight(grams_per_unit):
        return amount * grams_per_unit / _display_weight(unit_system)[1]
    return amount


def to_servings(
    amount: float,
    serving_size: float,
    grams_per_unit: float | None,
    unit_system: str,
) -> float:
    """
    Convert an amount the user entered into a number of servings.

    Parameters
    ----------
    amount : float
        The amount in ``amount_unit(...)``.
    serving_size : float
        Size of one serving, in the food's serving unit.
    grams_per_unit : float | None
        Grams in one of the food's serving units, or None if it is not a
        weight.
    unit_system : str
        Either ``"imperial"`` or ``"metric"``.

    Returns
    -------
    float
        Number of servings, rounded to the three decimals the database keeps.
    """
    if _is_weight(grams_per_unit):
        amount = amount * _display_weight(unit_system)[1] / grams_per_unit
    return round(amount / serving_size, 3)


def scale_entries(entries: pd.DataFrame, unit_system: str) -> pd.DataFrame:
    """
    Add amount and unit columns, and scale macros to the servings eaten.

    Parameters
    ----------
    entries : pd.DataFrame
        One row per log entry or ingredient, with columns ``item_name``,
        ``servings``, ``serving_size``, ``serving_unit``, ``grams_per_unit``
        and the per-serving macro columns in ``MACROS``.
    unit_system : str
        Either ``"imperial"`` or ``"metric"``.

    Returns
    -------
    pd.DataFrame
        Columns ``item_name``, ``amount``, ``unit`` and the macro columns
        (now totals for the amount eaten), with the same index as
        ``entries``.
    """
    out = pd.DataFrame(index=entries.index)
    out["item_name"] = entries["item_name"]
    out["amount"] = [
        to_amount(row.servings, row.serving_size, row.grams_per_unit, unit_system)
        for row in entries.itertuples()
    ]
    out["unit"] = [
        amount_unit(row.serving_unit, row.grams_per_unit, unit_system)
        for row in entries.itertuples()
    ]
    for column in MACROS:
        out[column] = entries["servings"] * entries[column]
    return out


def totals_row(scaled: pd.DataFrame) -> pd.DataFrame:
    """
    Build a one-row table with the macro totals of ``scale_entries`` output.

    Parameters
    ----------
    scaled : pd.DataFrame
        Output of ``scale_entries``.

    Returns
    -------
    pd.DataFrame
        A single row labelled ``"Total"`` with the same columns as
        ``scaled``. Amount and unit are left blank.
    """
    row = {"item_name": "Total", "amount": None, "unit": ""}
    row.update({column: scaled[column].sum() for column in MACROS})
    return pd.DataFrame([row])
