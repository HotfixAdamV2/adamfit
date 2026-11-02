"""Home page: a dashboard with today's weight and macros, and a grid of charts over time."""

from datetime import date

import pandas as pd
import streamlit as st

from adamfit import auth, charts, food_logs, weights
from adamfit.nutrition import scale_entries, totals_row
from adamfit.ui import macro_tiles
from adamfit.units import to_display_weight, weight_label

user = auth.current_user()
user_id = user["user_id"]
unit = weight_label(user["unit_system"])
today = date.today()

st.title("Fitness Dashboard", text_alignment="center")
st.caption(f"Today · {today:%A, %b %d, %Y}", text_alignment="center")

# ---- Today's weight ------------------------------------------------------
weigh_ins = weights.get_weights(user_id)
weigh_ins["weight"] = weigh_ins["weight_kg"].map(lambda kg: to_display_weight(kg, user["unit_system"]))
todays = weigh_ins[weigh_ins["weigh_date"] == pd.Timestamp(today)]

if todays.empty:
    with st.container(border=True):
        st.warning("You haven't logged your weight today.", icon=":material/monitor_weight:")
        # The path must match the one registered with st.Page in app.py
        st.page_link("pages/profile.py", label="Log it on My Profile (Weight tab)", icon=":material/person:")
else:
    st.metric("Today's weight", f"{todays['weight'].iloc[0]:.1f} {unit}", border=True, width="content")

# ---- Today's macros ------------------------------------------------------
# Load today's log and add up the macros. An empty log gives totals of zero.
log = food_logs.get_log(user_id, today)
totals = totals_row(scale_entries(log)).iloc[0]

macro_tiles(totals)

if log.empty:
    st.info("Nothing logged today yet. Add food on the Nutrition page.")

# ---- Charts over time ----------------------------------------------------
# The charts come from charts.py, shared with My Profile and Nutrition. The
# grid is always two cards wide; add a Card here to add a chart. Each key
# prefix keeps a card's widgets apart from the others and from other pages.
charts.chart_grid(
    [
        charts.Card(
            "Weight over time",
            "home_weight",
            lambda key: charts.show_weight_over_time(weigh_ins, unit, key),
        ),
        charts.Card(
            "Calories and macros over time",
            "home_macros",
            lambda key: charts.show_macros_over_time(user_id, key),
        ),
        charts.Card(
            "Weight change",
            "home_weight_change",
            lambda key: charts.show_weight_change(weigh_ins, unit, key),
        ),
    ]
)
