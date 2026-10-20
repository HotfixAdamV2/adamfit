"""Queries for the food, food_category and serving_unit tables."""

import pandas as pd
import streamlit as st
from psycopg import Connection, errors

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


# Longest category name the food_category table allows
CATEGORY_NAME_MAX = 50


@st.cache_data(ttl=3600, max_entries=100)
def get_categories(user_id: int) -> pd.DataFrame:
    """
    Load the active sub-categories a user can put foods in.

    These are the shared (built-in) sub-categories plus the user's own. Only
    sub-categories are returned, because every food sits in one. The result
    is cached for an hour per user; the add, rename and remove functions
    below clear it.

    Parameters
    ----------
    user_id : int
        The user whose own categories to include.

    Returns
    -------
    pd.DataFrame
        Columns ``category_id``, ``category_name``, ``parent_category_id``,
        ``parent_name``, ``label`` (e.g. ``"Protein › Poultry"``) and
        ``is_own`` (True for the user's own category), ordered by parent
        name then name.
    """
    rows = fetch_all(
        """
        SELECT
            fc.category_id,
            fc.category_name,
            fc.parent_category_id,
            parent.category_name AS parent_name,
            parent.category_name || ' › ' || fc.category_name AS label,
            fc.user_id IS NOT NULL AS is_own
        FROM food_category AS fc
        INNER JOIN food_category AS parent
            ON parent.category_id = fc.parent_category_id
        WHERE fc.is_active
            AND (fc.user_id IS NULL OR fc.user_id = %s)
        ORDER BY
            parent.category_name,
            fc.category_name
        """,
        (user_id,),
    )
    columns = ["category_id", "category_name", "parent_category_id", "parent_name", "label", "is_own"]
    return pd.DataFrame(rows, columns=columns)


@st.cache_data(ttl=3600, max_entries=100)
def get_parent_categories(user_id: int) -> pd.DataFrame:
    """
    Load the active top-level categories (those with no parent) a user can see.

    These are the shared ones plus the user's own, including own top-level
    categories that have no sub-categories yet. Cached like
    ``get_categories``.

    Parameters
    ----------
    user_id : int
        The user whose own categories to include.

    Returns
    -------
    pd.DataFrame
        Columns ``category_id``, ``category_name`` and ``is_own``, ordered
        by name.
    """
    rows = fetch_all(
        """
        SELECT
            category_id,
            category_name,
            user_id IS NOT NULL AS is_own
        FROM food_category
        WHERE parent_category_id IS NULL
            AND is_active
            AND (user_id IS NULL OR user_id = %s)
        ORDER BY category_name
        """,
        (user_id,),
    )
    return pd.DataFrame(rows, columns=["category_id", "category_name", "is_own"])


def _clear_category_cache(user_id: int) -> None:
    """
    Forget the cached categories for one user, so the next read sees a change.

    Parameters
    ----------
    user_id : int
        The user whose categories changed.
    """
    get_categories.clear(user_id)
    get_parent_categories.clear(user_id)


def _clean_category_name(name: str | None, what: str = "category") -> str:
    """
    Trim a category name and check its length.

    Parameters
    ----------
    name : str | None
        The name as typed.
    what : str, optional
        What the name is for, used in the error message, e.g.
        ``"top-level category"``.

    Returns
    -------
    str
        The name without spaces at either end.

    Raises
    ------
    ValueError
        If the name is empty or longer than ``CATEGORY_NAME_MAX``.
    """
    name = (name or "").strip()
    if not name:
        raise ValueError(f"Enter a name for the {what}.")
    if len(name) > CATEGORY_NAME_MAX:
        raise ValueError(f"A category name can be at most {CATEGORY_NAME_MAX} characters.")
    return name


def _category_error(e: errors.Error, name: str) -> ValueError | None:
    """
    Turn a database error about a category into a message for the user.

    The rules live in the database (migrations 000018 to 000021). Each one
    reports a SQLSTATE code and a constraint name, which is how they are
    told apart here.

    Parameters
    ----------
    e : errors.Error
        The error psycopg raised.
    name : str
        The category name involved, for the message.

    Returns
    -------
    ValueError | None
        An error with a friendly message, or None if ``e`` is not one of
        the category rules (the caller should then re-raise ``e``).
    """
    constraint = e.diag.constraint_name
    if e.sqlstate == "23505" and constraint == "unq_food_category_user_id_parent_category_id_category_name":
        return ValueError(f'"{name}" already exists here.')
    if e.sqlstate == "23503" and constraint == "fk_food_category_parent_category_id":
        return ValueError("That parent category isn't available. Choose another one.")
    if e.sqlstate == "23514" and constraint == "chk_food_category_user_id":
        return ValueError("The owner of a category can't be changed.")
    if e.sqlstate == "23514" and constraint == "chk_food_category_parent_category_id":
        return ValueError("A category can't be placed inside itself.")
    if e.sqlstate == "2BP01" and constraint == "chk_food_category_is_active":
        # The database's own message names the category and says what to do
        return ValueError(e.diag.message_primary)
    return None


def _insert_category(conn: Connection, user_id: int, name: str, parent_id: int | None) -> tuple[int, bool]:
    """
    Add one of the user's own categories, or bring back a removed one.

    Runs inside the caller's transaction. There is one row per owner, parent
    and name (ignoring capitals), active or not (migration 000021). So if the
    user removed a category with this name under this parent earlier, the
    INSERT clashes with that row and ``ON CONFLICT ... DO UPDATE`` makes it
    active again instead. The old row keeps its id and the capitals it was
    saved with.

    Parameters
    ----------
    conn : Connection
        An open connection from ``get_connection``. Nothing is committed here.
    user_id : int
        The owner of the category.
    name : str
        The cleaned name (see ``_clean_category_name``).
    parent_id : int | None
        The parent category, or None for a top-level category.

    Returns
    -------
    tuple[int, bool]
        The category's id, and True if a removed category was brought back
        (False for a brand new row).

    Raises
    ------
    ValueError
        If an active category with this name already exists here (yours or
        built-in), or the database rejects it for another reason.
    """
    try:
        # xmax is a PostgreSQL system column: 0 for a freshly inserted row,
        # non-zero for a row that ON CONFLICT updated
        row = conn.execute(
            """
            INSERT INTO food_category (
                user_id,
                category_name,
                parent_category_id
            )
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, parent_category_id, LOWER(category_name))
            DO UPDATE SET is_active = TRUE
                WHERE NOT food_category.is_active
            RETURNING
                category_id,
                xmax <> 0 AS brought_back
            """,
            (user_id, name, parent_id),
        ).fetchone()
    except errors.Error as e:
        friendly = _category_error(e, name)
        if friendly is None:
            raise
        raise friendly from e
    if row is None:
        # The clash was with an active row, so the WHERE above skipped the update
        raise ValueError(f'"{name}" already exists here.')
    return row["category_id"], row["brought_back"]


def _check_parent(conn: Connection, user_id: int, parent_id: int) -> None:
    """
    Make sure a chosen parent is still active and visible to the user.

    The database doesn't stop a category being added (or brought back)
    under a removed parent. The pickers only offer active parents, but a
    choice made before the parent was removed (e.g. in another browser tab)
    could still arrive here.

    Parameters
    ----------
    conn : Connection
        An open connection from ``get_connection``.
    user_id : int
        The user adding the category.
    parent_id : int
        The chosen parent category.

    Raises
    ------
    ValueError
        If the parent is removed, missing or another user's.
    """
    row = conn.execute(
        """
        SELECT
            category_id
        FROM food_category
        WHERE category_id = %s
            AND is_active
            AND (user_id IS NULL OR user_id = %s)
        """,
        (parent_id, user_id),
    ).fetchone()
    if row is None:
        raise ValueError("That parent category isn't available. Choose another one.")


def _create_category(
    conn: Connection,
    user_id: int,
    name: str,
    parent_id: int | None,
    new_parent_name: str | None,
) -> tuple[int, bool]:
    """
    Create a category, and its new top-level parent first if one is named.

    Either one can turn out to be a removed category of the user's that is
    brought back (see ``_insert_category``). Runs inside the caller's
    transaction, so if anything later fails both are rolled back with it.

    Parameters
    ----------
    conn : Connection
        An open connection from ``get_connection``.
    user_id : int
        The owner of the new categories.
    name : str
        Name of the category to create.
    parent_id : int | None
        Its parent, when the parent already exists. Ignored when
        ``new_parent_name`` is given.
    new_parent_name : str | None
        Create (or bring back) a top-level category with this name and use
        it as the parent.

    Returns
    -------
    tuple[int, bool]
        The id of the category called ``name``, and True if it was a
        removed category brought back.

    Raises
    ------
    ValueError
        If a name is empty, too long or already used, or the parent isn't
        available.
    """
    name = _clean_category_name(name)
    if new_parent_name is not None:
        new_parent_name = _clean_category_name(new_parent_name, "top-level category")
        parent_id, _ = _insert_category(conn, user_id, new_parent_name, None)
    elif parent_id is not None:
        _check_parent(conn, user_id, parent_id)
    return _insert_category(conn, user_id, name, parent_id)


def add_category(
    user_id: int,
    name: str,
    parent_id: int | None = None,
    new_parent_name: str | None = None,
) -> tuple[int, bool]:
    """
    Add one of the user's own food categories.

    If the user removed a category with the same name (ignoring capitals)
    under the same parent earlier, that one is brought back instead, with
    its old id and its old capitals.

    Parameters
    ----------
    user_id : int
        The owner of the new category.
    name : str
        The new category's name. Spaces at either end are removed.
    parent_id : int | None, optional
        The category to put it under (shared or the user's own). None makes
        a top-level category.
    new_parent_name : str | None, optional
        Also create (or bring back) a top-level category with this name, and
        put the new category under it. Both are saved in one transaction.

    Returns
    -------
    tuple[int, bool]
        The id of the category called ``name``, and True if it was a removed
        category brought back (False if it is new).

    Raises
    ------
    ValueError
        If a name is empty, longer than 50 characters or already used by an
        active category under the same parent, or the parent isn't
        available. The message is written for the user.
    """
    with get_connection() as conn:
        result = _create_category(conn, user_id, name, parent_id, new_parent_name)
    _clear_category_cache(user_id)
    return result


def _removed_name_exists(user_id: int, category_id: int, name: str) -> bool:
    """
    Check whether the user has a removed category with this name next to this one.

    Used only after a rename failed, to tell "you removed one with that name"
    apart from "an active one has that name".

    Parameters
    ----------
    user_id : int
        The owner of the category.
    category_id : int
        The category being renamed.
    name : str
        The name it was being renamed to.

    Returns
    -------
    bool
        True if one of the user's inactive categories under the same parent
        has this name (ignoring capitals).
    """
    rows = fetch_all(
        """
        SELECT
            other.category_id
        FROM food_category AS this
        INNER JOIN food_category AS other
            ON other.parent_category_id IS NOT DISTINCT FROM this.parent_category_id
        WHERE this.category_id = %s
            AND other.category_id <> this.category_id
            AND other.user_id = %s
            AND NOT other.is_active
            AND LOWER(other.category_name) = LOWER(%s)
        """,
        (category_id, user_id, name),
    )
    return bool(rows)


def rename_category(user_id: int, category_id: int, name: str) -> None:
    """
    Rename one of the user's own categories.

    Built-in categories can't be renamed: the query only matches rows the
    user owns (the database itself would allow it).

    Parameters
    ----------
    user_id : int
        The owner of the category.
    category_id : int
        The category to rename.
    name : str
        The new name. Spaces at either end are removed.

    Raises
    ------
    ValueError
        If the name is empty, too long or already used under the same
        parent (including by one of the user's removed categories, which
        gets its own message), or the category isn't one of the user's own
        active ones.
    """
    name = _clean_category_name(name)
    try:
        with get_connection() as conn:
            renamed = conn.execute(
                """
                UPDATE food_category
                SET category_name = %s
                WHERE category_id = %s
                    AND user_id = %s
                    AND is_active
                """,
                (name, category_id, user_id),
            ).rowcount
    except errors.Error as e:
        # Since migration 000021 a removed category still holds its name
        if e.sqlstate == "23505" and _removed_name_exists(user_id, category_id, name):
            raise ValueError(
                f'You removed a category called "{name}" earlier. Add it again to bring it back.'
            ) from e
        friendly = _category_error(e, name)
        if friendly is None:
            raise
        raise friendly from e
    if not renamed:
        raise ValueError("You can only rename your own categories.")
    _clear_category_cache(user_id)


def remove_category(user_id: int, category_id: int) -> None:
    """
    Remove one of the user's own categories.

    This only hides it (``is_active = FALSE``), so removed foods that were in
    it keep working in old logs and recipes. The database refuses while
    active foods or active sub-categories still use it. Adding a category
    with the same name under the same parent later brings this row back
    (see ``add_category``).

    Parameters
    ----------
    user_id : int
        The owner of the category.
    category_id : int
        The category to remove.

    Raises
    ------
    ValueError
        If the category is still in use (the database's message, e.g.
        'The category "Chips" still has active foods. Move or remove them
        first.'), or isn't one of the user's own active categories.
    """
    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                UPDATE food_category
                SET is_active = FALSE
                WHERE category_id = %s
                    AND user_id = %s
                    AND is_active
                RETURNING category_name
                """,
                (category_id, user_id),
            ).fetchone()
    except errors.Error as e:
        friendly = _category_error(e, "")
        if friendly is None:
            raise
        raise friendly from e
    if row is None:
        raise ValueError("You can only remove your own categories.")
    _clear_category_cache(user_id)


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


def _write_food_changes(
    conn: Connection,
    user_id: int,
    inserts: list[dict],
    updates: dict[int, dict],
    deletes: list[int],
) -> None:
    """
    Run the INSERT, UPDATE and soft-delete statements for a user's foods.

    Runs inside the caller's transaction and commits nothing itself, so it
    can share a transaction with other changes (see
    ``save_food_in_new_category``).

    Parameters
    ----------
    conn : Connection
        An open connection from ``get_connection``.
    user_id : int
        The user who owns the foods.
    inserts : list[dict]
        New foods, already cleaned by ``_clean_food``.
    updates : dict[int, dict]
        Cleaned new values for existing foods, keyed by ``food_id``.
    deletes : list[int]
        Ids of foods to remove.
    """
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


def _food_error(e: errors.Error) -> ValueError | None:
    """
    Turn a database error from saving foods into a message for the user.

    Parameters
    ----------
    e : errors.Error
        The error psycopg raised.

    Returns
    -------
    ValueError | None
        An error with a friendly message, or None if ``e`` is not one we
        expect (the caller should then re-raise ``e``).
    """
    if isinstance(e, errors.UniqueViolation):
        return ValueError("You already have a food with that name. Food names must be unique.")
    if isinstance(e, errors.NumericValueOutOfRange):
        return ValueError("One of the numbers is too large.")
    if isinstance(e, errors.ForeignKeyViolation):
        # fk_food_category_id: the category is gone or belongs to someone else
        return ValueError("That category isn't available. Choose another one.")
    return None


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
        If any food is invalid, two active foods would share a name, or a
        category isn't available. The message is written for the user.
    """
    inserts = [_clean_food(values) for values in inserts]
    updates = {food_id: _clean_food(values) for food_id, values in updates.items()}

    try:
        with get_connection() as conn:
            _write_food_changes(conn, user_id, inserts, updates, deletes)
    except errors.Error as e:
        friendly = _food_error(e)
        if friendly is None:
            raise
        raise friendly from e


def save_food_in_new_category(
    user_id: int,
    food_id: int | None,
    values: dict,
    category_name: str,
    parent_id: int | None = None,
    new_parent_name: str | None = None,
) -> tuple[int, bool]:
    """
    Create a new category and save one food in it, in a single transaction.

    Used by the food pop-up's "+ New category" choice. A removed category
    with the same name under the same parent is brought back instead of
    created (see ``add_category``). If the food can't be saved (e.g. its
    name is taken), the category change is rolled back too, so no empty
    category is left behind.

    Parameters
    ----------
    user_id : int
        The user who owns the food and the new category.
    food_id : int | None
        The food to update, or None to add a new one.
    values : dict
        The food's values, keyed by ``FOOD_FIELDS``. ``category_id`` is
        ignored and replaced by the new category's id.
    category_name : str
        Name of the new sub-category.
    parent_id : int | None, optional
        The existing top-level category to put it under.
    new_parent_name : str | None, optional
        Create a new top-level category with this name first and put the
        sub-category under it (``parent_id`` is then ignored).

    Returns
    -------
    tuple[int, bool]
        The sub-category's id, and True if it was a removed category
        brought back.

    Raises
    ------
    ValueError
        If the food or a category name is invalid or already used. The
        message is written for the user.
    """
    try:
        with get_connection() as conn:
            category_id, brought_back = _create_category(conn, user_id, category_name, parent_id, new_parent_name)
            # Checked inside the transaction because the category id is only
            # known now. A ValueError here rolls back the new category.
            food = _clean_food({**values, "category_id": category_id})
            if food_id is None:
                _write_food_changes(conn, user_id, [food], {}, [])
            else:
                _write_food_changes(conn, user_id, [], {food_id: food}, [])
    except errors.Error as e:
        friendly = _food_error(e)
        if friendly is None:
            raise
        raise friendly from e
    _clear_category_cache(user_id)
    return category_id, brought_back
