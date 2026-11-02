"""Queries for the exercise library.

Covers the exercise, exercise_muscle_group, exercise_image and muscle_group
tables, plus the exercise_type and equipment lookups. They live in one
module because they only make sense together, the same way ``foods.py``
covers food and food_category.

Every write function raises ``ValueError`` with a message written for the
user when the input is wrong or the database refuses it. The rules live in
the database (migrations 000025 to 000038). Each one reports a SQLSTATE
code and a constraint name, which is how the errors are told apart here.
"""

import pandas as pd
import streamlit as st
from psycopg import Connection, errors

from adamfit.db import fetch_all, fetch_one, get_connection

# Longest names the exercise and muscle_group tables allow
EXERCISE_NAME_MAX = 100
MUSCLE_GROUP_NAME_MAX = 50

# Pictures: the file types the uploader accepts, and the largest size the
# exercise_image table allows (5 MB)
IMAGE_FILE_TYPES = ["jpg", "jpeg", "png", "webp", "gif"]
IMAGE_MAX_BYTES = 5_242_880

# The exercise type that can have muscle tags
STRENGTH = "strength"


# ---- Lookups -----------------------------------------------------------


@st.cache_data(ttl=3600)
def get_exercise_types() -> dict[str, str]:
    """
    Load the kinds of exercise (strength, cardio).

    The list rarely changes, so it is cached for an hour.

    Returns
    -------
    dict[str, str]
        Type names keyed by ``type_code``, in display order, e.g.
        ``{"strength": "Strength", "cardio": "Cardio"}``.
    """
    rows = fetch_all(
        """
        SELECT
            type_code,
            type_name
        FROM exercise_type
        ORDER BY sort_order
        """
    )
    return {row["type_code"]: row["type_name"] for row in rows}


@st.cache_data(ttl=3600)
def get_equipment() -> dict[str, str]:
    """
    Load what an exercise can be done with (barbell, dumbbell...).

    Cached for an hour, like ``get_exercise_types``.

    Returns
    -------
    dict[str, str]
        Equipment names keyed by ``equipment_code``, in display order.
    """
    rows = fetch_all(
        """
        SELECT
            equipment_code,
            equipment_name
        FROM equipment
        ORDER BY sort_order
        """
    )
    return {row["equipment_code"]: row["equipment_name"] for row in rows}


# ---- Muscle groups -----------------------------------------------------


@st.cache_data(ttl=3600, max_entries=100)
def get_muscle_groups(user_id: int) -> pd.DataFrame:
    """
    Load the active muscle groups a user can tag exercises with.

    These are the built-in groups plus the user's own. Cached for an hour
    per user; the add, rename and remove functions below clear it.

    Parameters
    ----------
    user_id : int
        The user whose own groups to include.

    Returns
    -------
    pd.DataFrame
        Columns ``muscle_group_id``, ``muscle_group_name`` and ``is_own``
        (True for the user's own group), ordered by name.
    """
    rows = fetch_all(
        """
        SELECT
            muscle_group_id,
            muscle_group_name,
            user_id IS NOT NULL AS is_own
        FROM muscle_group
        WHERE is_active
            AND (user_id IS NULL OR user_id = %s)
        ORDER BY muscle_group_name
        """,
        (user_id,),
    )
    return pd.DataFrame(rows, columns=["muscle_group_id", "muscle_group_name", "is_own"])


def _clean_muscle_group_name(name: str | None) -> str:
    """
    Trim a muscle group name and check its length.

    Parameters
    ----------
    name : str | None
        The name as typed.

    Returns
    -------
    str
        The name without spaces at either end.

    Raises
    ------
    ValueError
        If the name is empty or longer than ``MUSCLE_GROUP_NAME_MAX``.
    """
    name = (name or "").strip()
    if not name:
        raise ValueError("Enter a name for the muscle group.")
    if len(name) > MUSCLE_GROUP_NAME_MAX:
        raise ValueError(f"A muscle group name can be at most {MUSCLE_GROUP_NAME_MAX} characters.")
    return name


def _muscle_group_error(e: errors.Error, name: str) -> ValueError | None:
    """
    Turn a database error about a muscle group into a message for the user.

    Parameters
    ----------
    e : errors.Error
        The error psycopg raised.
    name : str
        The group name involved, for the message.

    Returns
    -------
    ValueError | None
        An error with a friendly message, or None if ``e`` is not one of
        the muscle group rules (the caller should then re-raise ``e``).
    """
    constraint = e.diag.constraint_name
    if e.sqlstate == "23505" and constraint == "unq_muscle_group_user_id_muscle_group_name":
        # Also raised when the name matches a built-in group
        return ValueError(f'A muscle group called "{name}" already exists.')
    if e.sqlstate == "23514" and constraint == "chk_muscle_group_muscle_group_name":
        return ValueError("Enter a name for the muscle group.")
    return None


def _clear_muscle_group_cache(user_id: int) -> None:
    """
    Forget a user's cached muscle groups and exercises.

    The exercise list shows group names, so a renamed group must clear it too.

    Parameters
    ----------
    user_id : int
        The user whose groups changed.
    """
    get_muscle_groups.clear(user_id)
    get_exercises.clear(user_id)


def add_muscle_group(user_id: int, name: str) -> tuple[int, bool]:
    """
    Add one of the user's own muscle groups, or bring back a removed one.

    There is one row per owner and name (ignoring capitals), active or not.
    So if the user removed a group with this name earlier, the INSERT
    clashes with that row and ``ON CONFLICT ... DO UPDATE`` makes it active
    again instead. The old row keeps its id and the capitals it was saved with.

    Parameters
    ----------
    user_id : int
        The owner of the group.
    name : str
        The new group's name. Spaces at either end are removed.

    Returns
    -------
    tuple[int, bool]
        The group's id, and True if a removed group was brought back
        (False for a brand new one).

    Raises
    ------
    ValueError
        If the name is empty, too long, or already used by one of your
        active groups or a built-in group.
    """
    name = _clean_muscle_group_name(name)
    try:
        with get_connection() as conn:
            # xmax is a PostgreSQL system column: 0 for a freshly inserted
            # row, non-zero for a row that ON CONFLICT updated
            row = conn.execute(
                """
                INSERT INTO muscle_group (
                    user_id,
                    muscle_group_name
                )
                VALUES (%s, %s)
                ON CONFLICT (user_id, LOWER(muscle_group_name))
                DO UPDATE SET is_active = TRUE
                    WHERE NOT muscle_group.is_active
                RETURNING
                    muscle_group_id,
                    xmax <> 0 AS brought_back
                """,
                (user_id, name),
            ).fetchone()
    except errors.Error as e:
        friendly = _muscle_group_error(e, name)
        if friendly is None:
            raise
        raise friendly from e
    if row is None:
        # The clash was with an active row, so the WHERE above skipped the update
        raise ValueError(f'A muscle group called "{name}" already exists.')
    _clear_muscle_group_cache(user_id)
    return row["muscle_group_id"], row["brought_back"]


def _removed_group_exists(user_id: int, muscle_group_id: int, name: str) -> bool:
    """
    Check whether the user has another, removed muscle group with this name.

    Used only after a rename failed, to tell "you removed one with that
    name" apart from "an active one has that name".

    Parameters
    ----------
    user_id : int
        The owner of the group.
    muscle_group_id : int
        The group being renamed.
    name : str
        The name it was being renamed to.

    Returns
    -------
    bool
        True if one of the user's inactive groups has this name (ignoring capitals).
    """
    row = fetch_one(
        """
        SELECT
            muscle_group_id
        FROM muscle_group
        WHERE user_id = %s
            AND muscle_group_id <> %s
            AND NOT is_active
            AND LOWER(muscle_group_name) = LOWER(%s)
        """,
        (user_id, muscle_group_id, name),
    )
    return row is not None


def rename_muscle_group(user_id: int, muscle_group_id: int, name: str) -> None:
    """
    Rename one of the user's own muscle groups.

    Built-in groups can't be renamed: the query only matches rows the user owns.

    Parameters
    ----------
    user_id : int
        The owner of the group.
    muscle_group_id : int
        The group to rename.
    name : str
        The new name. Spaces at either end are removed.

    Raises
    ------
    ValueError
        If the name is empty, too long or already used (including by one
        of the user's removed groups, which gets its own message), or the
        group isn't one of the user's own active groups.
    """
    name = _clean_muscle_group_name(name)
    try:
        with get_connection() as conn:
            renamed = conn.execute(
                """
                UPDATE muscle_group
                SET muscle_group_name = %s
                WHERE muscle_group_id = %s
                    AND user_id = %s
                    AND is_active
                """,
                (name, muscle_group_id, user_id),
            ).rowcount
    except errors.Error as e:
        # A removed group still holds its name (the unique index covers it)
        if e.sqlstate == "23505" and _removed_group_exists(user_id, muscle_group_id, name):
            raise ValueError(
                f'You removed a muscle group called "{name}" earlier. Add it again to bring it back.'
            ) from e
        friendly = _muscle_group_error(e, name)
        if friendly is None:
            raise
        raise friendly from e
    if not renamed:
        raise ValueError("You can only rename your own muscle groups.")
    _clear_muscle_group_cache(user_id)


def _exercises_using_group(user_id: int, muscle_group_id: int) -> list[str]:
    """
    List the names of the user's active exercises tagged with a muscle group.

    Parameters
    ----------
    user_id : int
        The owner of the exercises.
    muscle_group_id : int
        The group to look for.

    Returns
    -------
    list[str]
        Exercise names, in alphabetical order.
    """
    rows = fetch_all(
        """
        SELECT
            e.exercise_name
        FROM exercise_muscle_group AS emg
        INNER JOIN exercise AS e
            ON e.exercise_id = emg.exercise_id
        WHERE emg.muscle_group_id = %s
            AND e.user_id = %s
            AND e.is_active
        ORDER BY e.exercise_name
        """,
        (muscle_group_id, user_id),
    )
    return [row["exercise_name"] for row in rows]


def remove_muscle_group(user_id: int, muscle_group_id: int) -> None:
    """
    Remove one of the user's own muscle groups.

    This only hides it (``is_active = FALSE``), so removed exercises that
    were tagged with it keep their tags. The database refuses while an
    active exercise is still tagged with it. Adding a group with the same
    name later brings this row back (see ``add_muscle_group``).

    Parameters
    ----------
    user_id : int
        The owner of the group.
    muscle_group_id : int
        The group to remove.

    Raises
    ------
    ValueError
        If active exercises still use the group (the message says how many
        and names them), or it isn't one of the user's own active groups.
    """
    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                UPDATE muscle_group
                SET is_active = FALSE
                WHERE muscle_group_id = %s
                    AND user_id = %s
                    AND is_active
                RETURNING muscle_group_name
                """,
                (muscle_group_id, user_id),
            ).fetchone()
    except errors.Error as e:
        if e.sqlstate == "2BP01" and e.diag.constraint_name == "chk_muscle_group_is_active":
            names = _exercises_using_group(user_id, muscle_group_id)
            shown = ", ".join(names[:5])
            if len(names) > 5:
                shown += f" and {len(names) - 5} more"
            raise ValueError(
                f"This muscle group is still used by {len(names)} "
                f"exercise{'s' if len(names) != 1 else ''}: {shown}. Untag them first."
            ) from e
        raise
    if row is None:
        raise ValueError("You can only remove your own muscle groups.")
    _clear_muscle_group_cache(user_id)


# ---- Exercises ---------------------------------------------------------


@st.cache_data(ttl=3600, max_entries=100)
def get_exercises(user_id: int) -> pd.DataFrame:
    """
    Load a user's active exercises with their muscle tags.

    Cached for an hour per user. Every function below that changes an
    exercise or a muscle group clears it.

    Parameters
    ----------
    user_id : int
        The user whose exercises to load.

    Returns
    -------
    pd.DataFrame
        Indexed by ``exercise_id``, ordered by name, with columns
        ``exercise_name``, ``exercise_type`` (code), ``type_name``,
        ``equipment`` (code), ``equipment_name``, ``instructions`` (an
        empty string when there are none: pandas would turn a missing value
        into NaN, which counts as True in an ``if``), ``primary_ids`` and ``primary_names`` (lists in the
        same order), ``secondary_ids`` and ``secondary_names``, and
        ``has_image`` (True when the exercise has a picture). Tags on
        removed muscle groups are included.
    """
    # FILTER keeps only the primary (or secondary) tags in each list. An
    # exercise with no tags gets NULL from ARRAY_AGG, so COALESCE turns it
    # into an empty list. The ids and names are sorted the same way, so
    # they line up.
    rows = fetch_all(
        """
        SELECT
            e.exercise_id,
            e.exercise_name,
            e.exercise_type,
            et.type_name,
            e.equipment,
            eq.equipment_name,
            COALESCE(e.instructions, '') AS instructions,
            COALESCE(
                ARRAY_AGG(mg.muscle_group_id ORDER BY mg.muscle_group_name) FILTER (WHERE emg.is_primary),
                '{}'
            ) AS primary_ids,
            COALESCE(
                ARRAY_AGG(mg.muscle_group_name ORDER BY mg.muscle_group_name) FILTER (WHERE emg.is_primary),
                '{}'
            ) AS primary_names,
            COALESCE(
                ARRAY_AGG(mg.muscle_group_id ORDER BY mg.muscle_group_name) FILTER (WHERE NOT emg.is_primary),
                '{}'
            ) AS secondary_ids,
            COALESCE(
                ARRAY_AGG(mg.muscle_group_name ORDER BY mg.muscle_group_name) FILTER (WHERE NOT emg.is_primary),
                '{}'
            ) AS secondary_names,
            EXISTS (
                SELECT
                    1
                FROM exercise_image AS ei
                WHERE ei.exercise_id = e.exercise_id
            ) AS has_image
        FROM exercise AS e
        INNER JOIN exercise_type AS et
            ON et.type_code = e.exercise_type
        INNER JOIN equipment AS eq
            ON eq.equipment_code = e.equipment
        LEFT JOIN exercise_muscle_group AS emg
            ON emg.exercise_id = e.exercise_id
        LEFT JOIN muscle_group AS mg
            ON mg.muscle_group_id = emg.muscle_group_id
        WHERE e.user_id = %s
            AND e.is_active
        GROUP BY
            e.exercise_id,
            et.type_name,
            eq.equipment_name
        ORDER BY e.exercise_name
        """,
        (user_id,),
    )
    columns = [
        "exercise_id",
        "exercise_name",
        "exercise_type",
        "type_name",
        "equipment",
        "equipment_name",
        "instructions",
        "primary_ids",
        "primary_names",
        "secondary_ids",
        "secondary_names",
        "has_image",
    ]
    return pd.DataFrame(rows, columns=columns).set_index("exercise_id")


@st.cache_data(ttl=3600, max_entries=10)
def get_exercise_image(user_id: int, exercise_id: int) -> dict | None:
    """
    Load an exercise's picture.

    Pictures can be a few MB, and the edit pop-up reruns on every click
    inside it, so the last few are cached. ``save_exercise`` clears the
    entry when the picture changes.

    Parameters
    ----------
    user_id : int
        The owner of the exercise. Another user's picture is never returned.
    exercise_id : int
        The exercise whose picture to load.

    Returns
    -------
    dict | None
        ``image_data`` (bytes), ``mime_type`` and ``file_name``, or None
        if the exercise has no picture.
    """
    row = fetch_one(
        """
        SELECT
            ei.image_data,
            ei.mime_type,
            ei.file_name
        FROM exercise_image AS ei
        INNER JOIN exercise AS e
            ON e.exercise_id = ei.exercise_id
        WHERE ei.exercise_id = %s
            AND e.user_id = %s
        """,
        (exercise_id, user_id),
    )
    if row is None:
        return None
    # psycopg returns BYTEA as a memoryview; bytes is easier to work with
    return {**row, "image_data": bytes(row["image_data"])}


def check_image(data: bytes) -> str:
    """
    Check an uploaded picture's size and work out its type from its contents.

    The type is read from the first few bytes of the file (every image
    format starts with its own "signature"), not from the file name, so a
    renamed file can't sneak through.

    Parameters
    ----------
    data : bytes
        The uploaded file's contents.

    Returns
    -------
    str
        The MIME type to store: ``"image/jpeg"``, ``"image/png"``,
        ``"image/webp"`` or ``"image/gif"``.

    Raises
    ------
    ValueError
        If the file is empty, bigger than 5 MB, or not one of those types.
    """
    if not data:
        raise ValueError("The picture is empty.")
    if len(data) > IMAGE_MAX_BYTES:
        size_mb = len(data) / 1024 / 1024
        raise ValueError(f"The picture is {size_mb:.1f} MB. Pictures can be at most 5 MB.")
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError("The picture must be a JPEG, PNG, WebP or GIF image.")


def _clean_exercise(values: dict) -> dict:
    """
    Check an exercise's values before saving.

    Parameters
    ----------
    values : dict
        ``exercise_name``, ``exercise_type``, ``equipment``,
        ``instructions``, ``primary_ids`` and ``secondary_ids``.

    Returns
    -------
    dict
        The same keys, with the name and instructions trimmed (empty
        instructions become None) and the tag lists made unique. Cardio
        exercises always get empty tag lists.

    Raises
    ------
    ValueError
        If the name is missing or too long, the type or equipment isn't
        one of the choices, or a muscle group is both primary and secondary.
    """
    name = (values.get("exercise_name") or "").strip()
    if not name:
        raise ValueError("Every exercise needs a name.")
    if len(name) > EXERCISE_NAME_MAX:
        raise ValueError(f"An exercise name can be at most {EXERCISE_NAME_MAX} characters.")
    if values.get("exercise_type") not in get_exercise_types():
        raise ValueError(f"Choose a type for {name}.")
    if values.get("equipment") not in get_equipment():
        raise ValueError(f"Choose the equipment for {name}.")

    # dict.fromkeys drops repeats but keeps the order
    primary_ids = list(dict.fromkeys(int(i) for i in values.get("primary_ids") or []))
    secondary_ids = list(dict.fromkeys(int(i) for i in values.get("secondary_ids") or []))
    if values["exercise_type"] != STRENGTH:
        # Only strength exercises have muscle tags (the database doesn't check this)
        primary_ids, secondary_ids = [], []
    if set(primary_ids) & set(secondary_ids):
        raise ValueError("A muscle group can be primary or secondary, not both.")

    instructions = (values.get("instructions") or "").strip()
    return {
        "exercise_name": name,
        "exercise_type": values["exercise_type"],
        "equipment": values["equipment"],
        "instructions": instructions or None,
        "primary_ids": primary_ids,
        "secondary_ids": secondary_ids,
    }


def _exercise_error(e: errors.Error) -> ValueError | None:
    """
    Turn a database error from saving an exercise into a message for the user.

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
    constraint = e.diag.constraint_name
    if e.sqlstate == "23505" and constraint == "unq_exercise_user_id_exercise_name":
        return ValueError("You already have an exercise with that name. Exercise names must be unique.")
    if e.sqlstate == "23503" and constraint == "fk_exercise_muscle_group_muscle_group_id":
        return ValueError("One of the muscle groups isn't available. Choose another one.")
    if e.sqlstate == "23503" and constraint in ("fk_exercise_exercise_type", "fk_exercise_equipment"):
        return ValueError("That type or equipment isn't available. Choose another one.")
    if e.sqlstate == "23514" and constraint == "chk_exercise_exercise_name":
        return ValueError("Every exercise needs a name.")
    if e.sqlstate == "23514" and constraint == "chk_exercise_image_mime_type":
        return ValueError("The picture must be a JPEG, PNG, WebP or GIF image.")
    if e.sqlstate == "23514" and constraint == "chk_exercise_image_image_data":
        return ValueError("Pictures can be at most 5 MB.")
    return None


def _write_tags(conn: Connection, exercise_id: int, primary_ids: list[int], secondary_ids: list[int]) -> None:
    """
    Replace an exercise's muscle tags with a new set.

    Deletes the old tags and inserts the new ones, inside the caller's
    transaction.

    Parameters
    ----------
    conn : Connection
        An open connection from ``get_connection``. Nothing is committed here.
    exercise_id : int
        The exercise to tag.
    primary_ids : list[int]
        Muscle groups the exercise mainly works.
    secondary_ids : list[int]
        Muscle groups it also works. Must not overlap ``primary_ids``.
    """
    conn.execute(
        """
        DELETE FROM exercise_muscle_group
        WHERE exercise_id = %s
        """,
        (exercise_id,),
    )
    tags = [(group_id, True) for group_id in primary_ids] + [(group_id, False) for group_id in secondary_ids]
    for group_id, is_primary in tags:
        conn.execute(
            """
            INSERT INTO exercise_muscle_group (
                exercise_id,
                muscle_group_id,
                is_primary
            )
            VALUES (%s, %s, %s)
            """,
            (exercise_id, group_id, is_primary),
        )


def _write_image(conn: Connection, exercise_id: int, data: bytes, mime_type: str, file_name: str | None) -> None:
    """
    Store (or replace) an exercise's picture, inside the caller's transaction.

    Parameters
    ----------
    conn : Connection
        An open connection from ``get_connection``. Nothing is committed here.
    exercise_id : int
        The exercise the picture belongs to.
    data : bytes
        The picture, already checked by ``check_image``.
    mime_type : str
        The type ``check_image`` returned.
    file_name : str | None
        The uploaded file's name, shown for information only.
    """
    conn.execute(
        """
        INSERT INTO exercise_image (
            exercise_id,
            image_data,
            mime_type,
            file_name
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (exercise_id)
        DO UPDATE SET
            image_data = EXCLUDED.image_data,
            mime_type = EXCLUDED.mime_type,
            file_name = EXCLUDED.file_name
        """,
        (exercise_id, data, mime_type, file_name[:255] if file_name else None),
    )


def save_exercise(
    user_id: int,
    exercise_id: int | None,
    values: dict,
    image_data: bytes | None = None,
    image_file_name: str | None = None,
    remove_image: bool = False,
) -> int:
    """
    Add or edit an exercise, with its muscle tags and picture, in one transaction.

    Either everything is saved or nothing is. The muscle tags are replaced
    by the ones in ``values``.

    Parameters
    ----------
    user_id : int
        The owner of the exercise.
    exercise_id : int | None
        The exercise to edit, or None to add a new one.
    values : dict
        ``exercise_name``, ``exercise_type`` (a code from
        ``get_exercise_types``), ``equipment`` (a code from
        ``get_equipment``), ``instructions`` (text or None),
        ``primary_ids`` and ``secondary_ids`` (lists of muscle group ids,
        ignored for cardio exercises).
    image_data : bytes | None, optional
        A new picture to store, replacing any old one. None keeps the
        current picture (unless ``remove_image`` is True).
    image_file_name : str | None, optional
        The new picture's file name.
    remove_image : bool, optional
        Delete the current picture. Ignored when ``image_data`` is given.

    Returns
    -------
    int
        The exercise's id.

    Raises
    ------
    ValueError
        If a value is invalid, the name is already used by another active
        exercise, a muscle group isn't available, the picture is the
        wrong type or too big, or the exercise isn't one of the user's own
        active exercises.
    """
    exercise = _clean_exercise(values)
    mime_type = check_image(image_data) if image_data is not None else None
    params = (exercise["exercise_name"], exercise["exercise_type"], exercise["equipment"], exercise["instructions"])

    try:
        with get_connection() as conn:
            if exercise_id is None:
                row = conn.execute(
                    """
                    INSERT INTO exercise (
                        exercise_name,
                        exercise_type,
                        equipment,
                        instructions,
                        user_id
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING exercise_id
                    """,
                    (*params, user_id),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    UPDATE exercise
                    SET
                        exercise_name = %s,
                        exercise_type = %s,
                        equipment = %s,
                        instructions = %s
                    WHERE user_id = %s
                        AND exercise_id = %s
                        AND is_active
                    RETURNING exercise_id
                    """,
                    (*params, user_id, exercise_id),
                ).fetchone()
                if row is None:
                    # Raising inside the with block rolls the transaction back
                    raise ValueError("That exercise isn't available any more.")
            saved_id = row["exercise_id"]

            _write_tags(conn, saved_id, exercise["primary_ids"], exercise["secondary_ids"])
            if image_data is not None:
                _write_image(conn, saved_id, image_data, mime_type, image_file_name)
            elif remove_image:
                conn.execute(
                    """
                    DELETE FROM exercise_image
                    WHERE exercise_id = %s
                    """,
                    (saved_id,),
                )
    except errors.Error as e:
        friendly = _exercise_error(e)
        if friendly is None:
            raise
        raise friendly from e

    get_exercises.clear(user_id)
    get_exercise_image.clear(user_id, saved_id)
    return saved_id


def remove_exercise(user_id: int, exercise_id: int) -> None:
    """
    Remove one of the user's exercises.

    This only hides it (``is_active = FALSE``), so its tags and picture are
    kept and its name can be used again straight away.

    Parameters
    ----------
    user_id : int
        The owner of the exercise.
    exercise_id : int
        The exercise to remove.

    Raises
    ------
    ValueError
        If the exercise isn't one of the user's own active exercises.
    """
    with get_connection() as conn:
        removed = conn.execute(
            """
            UPDATE exercise
            SET is_active = FALSE
            WHERE exercise_id = %s
                AND user_id = %s
                AND is_active
            """,
            (exercise_id, user_id),
        ).rowcount
    if not removed:
        raise ValueError("That exercise isn't available any more.")
    get_exercises.clear(user_id)
