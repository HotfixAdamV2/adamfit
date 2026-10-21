"""Queries for the google_health_connection table.

One row per user holds that user's Google Health (Fitbit) login: the OAuth
tokens, and the one-time ``oauth_state`` value used while a login is in
progress. Tokens are secrets: never print, log or show them.
"""

from datetime import datetime

from adamfit.db import execute, fetch_one, get_connection


def get_status(user_id: int) -> dict | None:
    """
    Fetch whether a user is connected, without any tokens.

    Use this for anything shown on screen.

    Parameters
    ----------
    user_id : int
        The user to look up.

    Returns
    -------
    dict | None
        ``is_connected`` (bool), ``connected_at`` and ``last_synced_at``
        (datetimes or None), or None if the user has never started
        connecting.
    """
    return fetch_one(
        """
        SELECT
            refresh_token IS NOT NULL AS is_connected,
            connected_at,
            last_synced_at
        FROM google_health_connection
        WHERE user_id = %s
        """,
        (user_id,),
    )


def get_tokens(user_id: int) -> dict | None:
    """
    Fetch a user's stored tokens.

    Parameters
    ----------
    user_id : int
        The user to look up.

    Returns
    -------
    dict | None
        ``refresh_token``, ``access_token`` and ``access_token_expires_at``
        (any may be None), or None if the user has no row.
    """
    return fetch_one(
        """
        SELECT
            refresh_token,
            access_token,
            access_token_expires_at
        FROM google_health_connection
        WHERE user_id = %s
        """,
        (user_id,),
    )


def set_oauth_state(user_id: int, state: str, expires_at: datetime) -> None:
    """
    Store the one-time state value for a login that is about to start.

    Creates the user's row if needed. Any earlier pending state is replaced.

    Parameters
    ----------
    user_id : int
        The user who is connecting.
    state : str
        Random value sent to Google and returned in the redirect.
    expires_at : datetime
        When the state stops being accepted.
    """
    execute(
        """
        INSERT INTO google_health_connection (
            user_id,
            oauth_state,
            oauth_state_expires_at
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET
            oauth_state = EXCLUDED.oauth_state,
            oauth_state_expires_at = EXCLUDED.oauth_state_expires_at
        """,
        (user_id, state, expires_at),
    )


def consume_oauth_state(state: str) -> dict | None:
    """
    Find the user a state value belongs to, and clear it so it can't be reused.

    Parameters
    ----------
    state : str
        The ``state`` value Google sent back in the redirect.

    Returns
    -------
    dict | None
        ``user_id`` and ``is_expired`` (bool), or None if no row has this
        state.
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                user_id,
                oauth_state_expires_at < CURRENT_TIMESTAMP AS is_expired
            FROM google_health_connection
            WHERE oauth_state = %s
            """,
            (state,),
        ).fetchone()
        if row is not None:
            conn.execute(
                """
                UPDATE google_health_connection
                SET
                    oauth_state = NULL,
                    oauth_state_expires_at = NULL
                WHERE user_id = %s
                """,
                (row["user_id"],),
            )
        return row


def save_tokens(
    user_id: int,
    refresh_token: str,
    access_token: str,
    access_token_expires_at: datetime,
    granted_scopes: str,
) -> None:
    """
    Store the tokens from a completed login and mark the user as connected.

    Parameters
    ----------
    user_id : int
        The user who connected.
    refresh_token : str
        Long-lived token used to get new access tokens.
    access_token : str
        Short-lived token sent with each API call.
    access_token_expires_at : datetime
        When ``access_token`` stops working.
    granted_scopes : str
        Space-separated permissions the user approved.
    """
    execute(
        """
        INSERT INTO google_health_connection (
            user_id,
            refresh_token,
            access_token,
            access_token_expires_at,
            granted_scopes,
            connected_at
        )
        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id) DO UPDATE
        SET
            refresh_token = EXCLUDED.refresh_token,
            access_token = EXCLUDED.access_token,
            access_token_expires_at = EXCLUDED.access_token_expires_at,
            granted_scopes = EXCLUDED.granted_scopes,
            connected_at = EXCLUDED.connected_at
        """,
        (user_id, refresh_token, access_token, access_token_expires_at, granted_scopes),
    )


def save_access_token(user_id: int, access_token: str, expires_at: datetime) -> None:
    """
    Store a refreshed access token.

    Parameters
    ----------
    user_id : int
        The user the token belongs to.
    access_token : str
        The new access token.
    expires_at : datetime
        When it stops working.
    """
    execute(
        """
        UPDATE google_health_connection
        SET
            access_token = %s,
            access_token_expires_at = %s
        WHERE user_id = %s
        """,
        (access_token, expires_at, user_id),
    )


def mark_synced(user_id: int) -> None:
    """
    Record that a sync just finished.

    Parameters
    ----------
    user_id : int
        The user who synced.
    """
    execute(
        """
        UPDATE google_health_connection
        SET last_synced_at = CURRENT_TIMESTAMP
        WHERE user_id = %s
        """,
        (user_id,),
    )


def clear_tokens(user_id: int) -> None:
    """
    Forget a user's tokens, which disconnects them. The row is kept.

    Parameters
    ----------
    user_id : int
        The user to disconnect.
    """
    execute(
        """
        UPDATE google_health_connection
        SET
            refresh_token = NULL,
            access_token = NULL,
            access_token_expires_at = NULL,
            granted_scopes = NULL
        WHERE user_id = %s
        """,
        (user_id,),
    )
