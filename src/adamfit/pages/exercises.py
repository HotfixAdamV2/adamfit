"""Exercises page: lists the exercises stored in the database."""

import streamlit as st

from adamfit.db import fetch_all

st.title("Exercises")

rows = fetch_all(
    """
    SELECT
        exercise_id,
        exercise_name,
        muscle_group
    FROM exercise
    ORDER BY exercise_name
    """
)
st.dataframe(rows, hide_index=True)
