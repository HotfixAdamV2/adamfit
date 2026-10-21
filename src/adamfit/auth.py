"""Password hashing and login state.

Passwords are hashed with Argon2. Who is logged in is kept in
``st.session_state``, which belongs to one browser tab and is cleared when the
tab is refreshed or closed.
"""

import streamlit as st
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from adamfit import users

_hasher = PasswordHasher()

# Checked when the username does not exist, so a wrong username takes as long
# as a wrong password and does not reveal which usernames are real.
_DUMMY_HASH = _hasher.hash("not-a-real-password")

_SESSION_KEY = "user_id"


def hash_password(password: str) -> str:
    """
    Hash a password for storage.

    Parameters
    ----------
    password : str
        The plain-text password.

    Returns
    -------
    str
        An Argon2 hash string, safe to store in the database.
    """
    return _hasher.hash(password)


def authenticate(username: str, password: str) -> int | None:
    """
    Check a username and password.

    On success the login time is recorded, and the stored hash is upgraded if
    Argon2's recommended settings have changed since it was made.

    Parameters
    ----------
    username : str
        Username as typed (case-insensitive).
    password : str
        Password as typed.

    Returns
    -------
    int | None
        The user's id if the credentials are correct, otherwise None.
    """
    record = users.get_login_record(username)
    try:
        _hasher.verify(record["password_hash"] if record else _DUMMY_HASH, password)
    except VerificationError:
        return None
    if record is None:
        return None

    if _hasher.check_needs_rehash(record["password_hash"]):
        users.update_password_hash(record["user_id"], hash_password(password))
    users.record_login(record["user_id"])
    return record["user_id"]


def log_in(user_id: int) -> None:
    """
    Mark a user as logged in for this browser session.

    Parameters
    ----------
    user_id : int
        The id returned by ``authenticate``.
    """
    st.session_state[_SESSION_KEY] = user_id


def log_out() -> None:
    """
    Log the current user out by clearing everything in this session.
    """
    st.session_state.clear()


def current_user_id() -> int | None:
    """
    Return the id of the logged-in user.

    Returns
    -------
    int | None
        The user's id, or None if nobody is logged in.
    """
    return st.session_state.get(_SESSION_KEY)


def current_user() -> dict:
    """
    Load the logged-in user's profile fresh from the database.

    Pages call this to get the user they are showing. ``app.py`` only lets
    logged-in users reach those pages, so a user is always present.

    Returns
    -------
    dict
        The user's profile (see ``adamfit.users.get_user``).
    """
    return users.get_user(current_user_id())
