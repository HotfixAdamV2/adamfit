"""Home page: a dashboard showing today's macronutrient totals."""

from datetime import date

import streamlit as st

from adamfit import food_logs
from adamfit.nutrition import scale_entries, totals_row
from adamfit.ui import macro_tiles

user_id = st.session_state["user_id"]
today = date.today()

st.title("Fitness Dashboard", text_alignment="center")
st.caption(f"Today's macros · {today:%A, %b %d, %Y}", text_alignment="center")

# Load today's log and add up the macros. An empty log gives totals of zero.
log = food_logs.get_log(user_id, today)
totals = totals_row(scale_entries(log)).iloc[0]

macro_tiles(totals)

if log.empty:
    st.info("Nothing logged today yet. Add food on the Nutrition page.")
