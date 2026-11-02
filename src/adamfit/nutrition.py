"""Shared nutrition maths: servings, amounts and macro totals.

Every food has one fixed serving (e.g. 4 oz, or 1 tbsp) and its macros are
for that serving. Recipes and log entries store a number of servings. These
helpers turn servings into the amount a person actually ate (e.g. 8 oz) and
scale the macros to match.

Amounts are always in the food's own serving unit (g, oz, cup, bar, ...).
The user's imperial/metric setting only applies to body measurements (see
``units.py``), never to foods.

Recipes are treated as a food whose serving is "1 <serving label>".
"""

import ast
import math
import operator

import pandas as pd

# Macro columns, in display order, with their labels. Tiles, tables and the
# Foods editor all follow this order. SQL never relies on it: queries name
# their columns, and rows are read by column name.
MACROS = {
    "fat_g": "Fat (g)",
    "carbs_g": "Carbs (g)",
    "protein_g": "Protein (g)",
    "fiber_g": "Fiber (g)",
    "calories": "Calories",
}

# Servings are stored as NUMERIC(8, 3) in food_log and recipe_ingredient, so
# typed amounts are rounded to 3 decimals, and expressions are kept short.
SERVINGS_DECIMALS = 3
MAX_SERVINGS_TEXT = 50

# The only arithmetic ``parse_servings`` allows, mapped to the function that
# does it. Anything else (powers, names, function calls...) is rejected.
_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _evaluate(node: ast.AST) -> float:
    """
    Work out the value of one piece of a parsed sum.

    Parameters
    ----------
    node : ast.AST
        A node from ``ast.parse(..., mode="eval")``.

    Returns
    -------
    float
        The value of that node and everything under it.

    Raises
    ------
    ValueError
        If the node is anything other than a number, ``+ - * /`` or a sign.
    ZeroDivisionError
        If the sum divides by zero.
    """
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    # bool is a kind of int in Python, so True/False are ruled out by name
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        return _BINARY_OPS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_evaluate(node.operand))
    raise ValueError("Only numbers and + - * / are allowed")


def parse_servings(text: str) -> float | None:
    """
    Turn what was typed in a Servings box into a number of servings.

    Accepts a plain number (``"1.5"``) or a sum using ``+ - * /`` and
    brackets (``"4.2/1.5"``, ``"150*2/140"``), so you can type the weight
    you ate divided by the serving size.

    Parameters
    ----------
    text : str
        The text from the box.

    Returns
    -------
    float | None
        The number of servings, rounded to ``SERVINGS_DECIMALS`` decimals
        (the database column's scale). None if the text is empty, too long,
        not a valid sum, divides by zero, comes out infinitely large, or
        comes to zero or less (also after rounding).
    """
    text = (text or "").strip()
    if not text or len(text) > MAX_SERVINGS_TEXT:
        return None
    # eval() would run any Python the user typed. Instead, ast.parse only
    # reads the text into a tree, and _evaluate works out the value itself,
    # allowing nothing but numbers and + - * /.
    try:
        value = _evaluate(ast.parse(text, mode="eval"))
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
        return None
    # Huge sums such as 1e308*10 come out as infinity, which is not a number
    if not math.isfinite(value):
        return None
    value = round(value, SERVINGS_DECIMALS)
    if value <= 0:
        return None
    return value


def to_amount(servings: float, serving_size: float) -> float:
    """
    Convert a number of servings into the amount shown to the user.

    Parameters
    ----------
    servings : float
        Number of servings, as stored in the database.
    serving_size : float
        Size of one serving, in the food's serving unit.

    Returns
    -------
    float
        The amount in the food's own serving unit, e.g. 2 servings of a
        4 oz food is 8 (oz).
    """
    return servings * serving_size


def format_amount(servings: float, serving_size: float, unit: str) -> str:
    """
    Describe the amount eaten as text, such as ``"45 g"`` or ``"1.5 bowl"``.

    Parameters
    ----------
    servings : float
        Number of servings eaten.
    serving_size : float
        Size of one serving, in the food's serving unit.
    unit : str
        The food's serving unit (or a recipe's serving label).

    Returns
    -------
    str
        The amount rounded to two decimals, without trailing zeros, then
        the unit.
    """
    amount = round(to_amount(servings, serving_size), 2)
    return f"{amount:g} {unit}"


def scale_entries(entries: pd.DataFrame) -> pd.DataFrame:
    """
    Add an amount column, and scale macros to the servings eaten.

    Parameters
    ----------
    entries : pd.DataFrame
        One row per log entry or ingredient, with columns ``item_name``,
        ``servings``, ``serving_size``, ``serving_unit`` and the per-serving
        macro columns in ``MACROS``.

    Returns
    -------
    pd.DataFrame
        Columns ``item_name``, ``servings``, ``amount`` (text such as
        ``"45 g"``, see ``format_amount``) and the macro columns (now totals
        for the servings eaten), with the same index as ``entries``.
    """
    out = pd.DataFrame(index=entries.index)
    out["item_name"] = entries["item_name"]
    out["servings"] = entries["servings"]
    out["amount"] = [
        format_amount(servings, size, unit)
        for servings, size, unit in zip(
            entries["servings"], entries["serving_size"], entries["serving_unit"]
        )
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
        ``scaled``. Servings and amount are left blank, because adding up
        servings of different foods means nothing.
    """
    row = {"item_name": "Total", "servings": None, "amount": ""}
    row.update({column: scaled[column].sum() for column in MACROS})
    return pd.DataFrame([row])
