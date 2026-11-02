"""Queries and calculations for the user_weight table."""

from datetime import date

import pandas as pd

from adamfit.db import execute, fetch_all, get_connection

# How each source value is shown on screen
SOURCE_LABELS = {"manual": "Manual", "google_health": "Fitbit"}


def save_weight(user_id: int, weigh_date: date, weight_kg: float) -> None:
    """
    Record a weigh-in typed in by hand, replacing any entry for the same date.

    The row's source becomes ``'manual'``, even if it was synced before.

    Parameters
    ----------
    user_id : int
        The user the weigh-in belongs to.
    weigh_date : date
        The day of the weigh-in.
    weight_kg : float
        Weight in kilograms.
    """
    execute(
        """
        INSERT INTO user_weight (
            user_id,
            weigh_date,
            weight_kg,
            source
        )
        VALUES (%s, %s, %s, 'manual')
        ON CONFLICT ON CONSTRAINT unq_user_weight_user_id_weigh_date
        DO UPDATE
        SET
            weight_kg = EXCLUDED.weight_kg,
            source = EXCLUDED.source
        """,
        (user_id, weigh_date, round(weight_kg, 3)),
    )


def save_synced_weights(user_id: int, weights_by_day: dict[date, float]) -> None:
    """
    Store weigh-ins synced from Google Health, one per day.

    A synced value replaces whatever is stored for that day, including a
    weigh-in typed in by hand. All rows are saved together, so either all
    of them are saved or none are.

    Parameters
    ----------
    user_id : int
        The user the weigh-ins belong to.
    weights_by_day : dict[date, float]
        Weight in kilograms, keyed by the day of the weigh-in.
    """
    with get_connection() as conn:
        for weigh_date, weight_kg in weights_by_day.items():
            conn.execute(
                """
                INSERT INTO user_weight (
                    user_id,
                    weigh_date,
                    weight_kg,
                    source
                )
                VALUES (%s, %s, %s, 'google_health')
                ON CONFLICT ON CONSTRAINT unq_user_weight_user_id_weigh_date
                DO UPDATE
                SET
                    weight_kg = EXCLUDED.weight_kg,
                    source = EXCLUDED.source
                """,
                (user_id, weigh_date, round(weight_kg, 3)),
            )


def delete_weight(user_id: int, weigh_date: date) -> None:
    """
    Delete the weigh-in for one date.

    Parameters
    ----------
    user_id : int
        The user the weigh-in belongs to.
    weigh_date : date
        The day to delete.
    """
    execute(
        """
        DELETE FROM user_weight
        WHERE user_id = %s
            AND weigh_date = %s
        """,
        (user_id, weigh_date),
    )


def get_weights(user_id: int) -> pd.DataFrame:
    """
    Load every weigh-in for a user, oldest first.

    Parameters
    ----------
    user_id : int
        The user whose weigh-ins to load.

    Returns
    -------
    pd.DataFrame
        Columns ``weigh_date`` (datetime), ``weight_kg`` (float) and
        ``source`` (``'manual'`` or ``'google_health'``). Empty if the user
        has no weigh-ins.
    """
    rows = fetch_all(
        """
        SELECT
            weigh_date,
            weight_kg,
            source
        FROM user_weight
        WHERE user_id = %s
        ORDER BY weigh_date
        """,
        (user_id,),
    )
    df = pd.DataFrame(rows, columns=["weigh_date", "weight_kg", "source"])
    df["weigh_date"] = pd.to_datetime(df["weigh_date"])
    df["weight_kg"] = df["weight_kg"].astype(float)
    return df

