"""Queries for the app_user table."""

from datetime import date

from adamfit.db import execute, fetch_one

# Columns that are safe to keep in the session (never the password hash)
_PUBLIC_COLUMNS = """
    user_id,
    username,
    sex,
    height_cm,
    birth_date,
    unit_system
"""


def get_user(user_id: int) -> dict | None:
    """
    Fetch a user's profile by id.

    Parameters
    ----------
    user_id : int
        The user's id.

    Returns
    -------
    dict | None
        The user's profile (without the password hash), or None if not found.
    """
    return fetch_one(
        f"""
        SELECT {_PUBLIC_COLUMNS}
        FROM app_user
        WHERE user_id = %s
        """,
        (user_id,),
    )


def get_login_record(username: str) -> dict | None:
    """
    Fetch the id and password hash for an active user, for checking a login.

    Parameters
    ----------
    username : str
        The username typed on the login page (case-insensitive).

    Returns
    -------
    dict | None
        ``user_id`` and ``password_hash``, or None if no active user matches.
    """
    return fetch_one(
        """
        SELECT
            user_id,
            password_hash
        FROM app_user
        WHERE username = %s
            AND is_active
        """,
        (username.strip().lower(),),
    )


def create_user(username: str, password_hash: str) -> int:
    """
    Insert a new user and return their id.

    Parameters
    ----------
    username : str
        Desired username. Stored in lowercase.
    password_hash : str
        Argon2 hash of the user's password (see ``adamfit.auth.hash_password``).

    Returns
    -------
    int
        The new user's id.
    """
    row = fetch_one(
        """
        INSERT INTO app_user (
            username,
            password_hash
        )
        VALUES (%s, %s)
        RETURNING user_id
        """,
        (username.strip().lower(), password_hash),
    )
    return row["user_id"]


def update_profile(
    user_id: int,
    sex: str | None,
    height_cm: float | None,
    birth_date: date | None,
) -> None:
    """
    Save a user's body details.

    Parameters
    ----------
    user_id : int
        The user to update.
    sex : str | None
        ``"male"``, ``"female"`` or None.
    height_cm : float | None
        Height in centimetres, or None if unknown.
    birth_date : date | None
        Date of birth, or None if not given.
    """
    execute(
        """
        UPDATE app_user
        SET
            sex = %s,
            height_cm = %s,
            birth_date = %s
        WHERE user_id = %s
        """,
        (sex, height_cm, birth_date, user_id),
    )


def update_unit_system(user_id: int, unit_system: str) -> None:
    """
    Save whether a user prefers imperial or metric units.

    Parameters
    ----------
    user_id : int
        The user to update.
    unit_system : str
        Either ``"imperial"`` or ``"metric"``.
    """
    execute(
        """
        UPDATE app_user
        SET unit_system = %s
        WHERE user_id = %s
        """,
        (unit_system, user_id),
    )


def update_password_hash(user_id: int, password_hash: str) -> None:
    """
    Replace a user's stored password hash.

    Parameters
    ----------
    user_id : int
        The user to update.
    password_hash : str
        The new Argon2 hash.
    """
    execute(
        """
        UPDATE app_user
        SET password_hash = %s
        WHERE user_id = %s
        """,
        (password_hash, user_id),
    )


def record_login(user_id: int) -> None:
    """
    Stamp the time of a successful login.

    Parameters
    ----------
    user_id : int
        The user who just logged in.
    """
    execute(
        """
        UPDATE app_user
        SET last_login_at = CURRENT_TIMESTAMP
        WHERE user_id = %s
        """,
        (user_id,),
    )
