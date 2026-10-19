"""My Profile page: body details, weigh-ins, and a weight-over-time chart."""

from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from adamfit import auth, users, weights
from adamfit.ui import flash, show_flash
from adamfit.units import (
    cm_to_ft_in,
    from_display_weight,
    ft_in_to_cm,
    to_display_weight,
    weight_label,
)

# Chart period choices and how many days back each one shows (None = all)
PERIODS = {"1M": 30, "3M": 91, "6M": 182, "1Y": 365, "All": None}
UNIT_LABELS = {"imperial": "Pounds (lb, ft/in)", "metric": "Kilograms (kg, cm)"}
MAX_WEIGHT_KG = 699.0

user = auth.current_user()
user_id = user["user_id"]
unit_system = user["unit_system"]
unit = weight_label(unit_system)

st.title("My Profile")
show_flash()


# ---- Units -------------------------------------------------------------
def save_unit_system() -> None:
    """
    Save the unit choice as soon as the user changes it.
    """
    users.update_unit_system(auth.current_user_id(), st.session_state["unit_choice"])


st.segmented_control(
    "Units",
    options=list(UNIT_LABELS),
    format_func=UNIT_LABELS.get,
    default=unit_system,
    required=True,
    key="unit_choice",
    on_change=save_unit_system,
)

# ---- Body details ------------------------------------------------------
st.subheader("Body details")

with st.form("profile_form"):
    sex_options = [None, "male", "female"]
    sex = st.selectbox(
        "Sex",
        sex_options,
        index=sex_options.index(user["sex"]),
        format_func=lambda s: "Not set" if s is None else s.title(),
    )

    stored_cm = float(user["height_cm"]) if user["height_cm"] else None
    if unit_system == "imperial":
        stored_ft, stored_in = cm_to_ft_in(stored_cm) if stored_cm else (None, None)
        col_ft, col_in = st.columns(2)
        feet = col_ft.number_input("Height (ft)", min_value=0, max_value=8, value=stored_ft, step=1)
        inches = col_in.number_input(
            "Height (in)", min_value=0.0, max_value=11.9, value=stored_in, step=0.5, format="%.1f"
        )
    else:
        height_cm_input = st.number_input(
            "Height (cm)", min_value=0.0, max_value=299.9, value=stored_cm, step=0.5, format="%.1f"
        )

    birth_date = st.date_input(
        "Birth date",
        value=user["birth_date"],
        min_value=date(1900, 1, 2),
        max_value=date.today(),
    )

    if st.form_submit_button("Save details"):
        if unit_system == "imperial":
            height_cm = ft_in_to_cm(feet or 0, inches or 0)
        else:
            height_cm = height_cm_input or 0
        users.update_profile(user_id, sex, round(height_cm, 1) or None, birth_date)
        flash("Body details saved.")
        st.rerun()

# ---- Log weight --------------------------------------------------------
st.subheader("Log weight")

df = weights.get_weights(user_id)
df["weight"] = df["weight_kg"].map(lambda kg: to_display_weight(kg, unit_system))

with st.form("weight_form"):
    col_date, col_weight = st.columns(2)
    weigh_date = col_date.date_input("Date", value=date.today(), max_value=date.today())
    weight = col_weight.number_input(
        f"Weight ({unit})",
        min_value=0.1,
        max_value=round(to_display_weight(MAX_WEIGHT_KG, unit_system), 1),
        value=round(float(df["weight"].iloc[-1]), 1) if not df.empty else None,
        step=0.1,
        format="%.1f",
    )
    st.caption("Entering a date that already has a weight replaces it.")

    if st.form_submit_button("Save weight", type="primary"):
        if weight is None:
            st.error("Enter a weight first.")
        else:
            weights.save_weight(user_id, weigh_date, from_display_weight(weight, unit_system))
            flash(f"Saved {weight:.1f} {unit} for {weigh_date:%b %d, %Y}.")
            st.rerun()

if not df.empty:
    with st.expander("Delete an entry"):
        entry_dates = df["weigh_date"].dt.date.tolist()[::-1]
        to_delete = st.selectbox("Date", entry_dates, format_func=lambda d: f"{d:%b %d, %Y}")
        if st.button("Delete", icon=":material/delete:"):
            weights.delete_weight(user_id, to_delete)
            flash(f"Deleted the entry for {to_delete:%b %d, %Y}.")
            st.rerun()

# ---- Weight over time --------------------------------------------------
st.subheader("Weight over time")

if df.empty:
    st.info("No weigh-ins yet. Log one above to see your chart.")
    st.stop()

col_period, col_window = st.columns([3, 2])
period = col_period.segmented_control("Time period", list(PERIODS), default="3M", required=True)
window_days = col_window.number_input(
    "Rolling average (days)", min_value=1, max_value=90, value=7, step=1
)

# Average over the full history first, so the start of the chart is accurate
df = weights.add_rolling_average(df, "weight", window_days)
days_back = PERIODS[period]
if days_back is None:
    view = df
else:
    view = df[df["weigh_date"] >= pd.Timestamp(date.today() - timedelta(days=days_back))]

latest = df.iloc[-1]
previous_weight = df["weight"].iloc[-2] if len(df) > 1 else None
col_current, col_avg, col_change = st.columns(3)
col_current.metric(
    "Current weight",
    f"{latest['weight']:.1f} {unit}",
    delta=f"{latest['weight'] - previous_weight:+.1f} {unit}" if previous_weight is not None else None,
    delta_color="off",
    help=f"Most recent weigh-in ({latest['weigh_date']:%b %d, %Y}), compared with the one before.",
)
col_avg.metric(f"{window_days}-day average", f"{latest['rolling_avg']:.1f} {unit}")
if len(view) > 1:
    col_change.metric(
        f"Change ({period})",
        f"{view['weight'].iloc[-1] - view['weight'].iloc[0]:+.1f} {unit}",
    )

if view.empty:
    st.info("No weigh-ins in this time period. Try a longer one.")
    st.stop()

avg_label = f"{window_days}-day average"
long = view.melt(
    id_vars="weigh_date",
    value_vars=["weight", "rolling_avg"],
    var_name="series",
    value_name="value",
)
long["series"] = long["series"].map({"weight": "Weigh-in", "rolling_avg": avg_label})

base = alt.Chart(long).encode(
    x=alt.X("weigh_date:T", title="Date"),
    y=alt.Y("value:Q", title=f"Weight ({unit})", scale=alt.Scale(zero=False)),
    color=alt.Color("series:N", title=None, legend=alt.Legend(orient="bottom")),
    tooltip=[
        alt.Tooltip("weigh_date:T", title="Date"),
        alt.Tooltip("series:N", title="Series"),
        alt.Tooltip("value:Q", title=unit, format=".1f"),
    ],
)
weigh_ins = base.transform_filter(alt.datum.series == "Weigh-in").mark_line(
    point=True, opacity=0.5
)
average = base.transform_filter(alt.datum.series == avg_label).mark_line(strokeWidth=3)
st.altair_chart(weigh_ins + average)

with st.expander("Entries in this period"):
    st.dataframe(
        view[["weigh_date", "weight"]].iloc[::-1],
        hide_index=True,
        column_config={
            "weigh_date": st.column_config.DateColumn("Date", format="MMM D, YYYY"),
            "weight": st.column_config.NumberColumn(f"Weight ({unit})", format="%.1f"),
        },
    )
