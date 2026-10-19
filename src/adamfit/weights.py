"""Queries and calculations for the user_weight table."""

from datetime import date

import pandas as pd

from adamfit.db import execute, fetch_all


def save_weight(user_id: int, weigh_date: date, weight_kg: float) -> None:
    """
    Record a weigh-in, replacing any existing entry for the same date.

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
            weight_kg
        )
        VALUES (%s, %s, %s)
        ON CONFLICT ON CONSTRAINT unq_user_weight_user_id_weigh_date
        DO UPDATE SET weight_kg = EXCLUDED.weight_kg
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
        Columns ``weigh_date`` (datetime) and ``weight_kg`` (float). Empty if
        the user has no weigh-ins.
    """
    rows = fetch_all(
        """
        SELECT
            weigh_date,
            weight_kg
        FROM user_weight
        WHERE user_id = %s
        ORDER BY weigh_date
        """,
        (user_id,),
    )
    df = pd.DataFrame(rows, columns=["weigh_date", "weight_kg"])
    df["weigh_date"] = pd.to_datetime(df["weigh_date"])
    df["weight_kg"] = df["weight_kg"].astype(float)
    return df


def add_rolling_average(df: pd.DataFrame, value_column: str, window_days: int) -> pd.DataFrame:
    """
    Add a time-based rolling average column.

    The window covers calendar days, not number of entries, so skipped days
    are handled correctly: a 7-day average on any date is the mean of all
    weigh-ins in the 7 days ending on that date.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain a ``weigh_date`` datetime column, sorted oldest first.
    value_column : str
        Name of the column to average.
    window_days : int
        Size of the window in days.

    Returns
    -------
    pd.DataFrame
        A copy of ``df`` with an added ``rolling_avg`` column.
    """
    out = df.copy()
    out["rolling_avg"] = (
        out.set_index("weigh_date")[value_column].rolling(f"{window_days}D").mean().to_numpy()
    )
    return out
