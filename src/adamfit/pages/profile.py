"""My Profile page: a units toggle, then a Body details tab and a Weight tab (weigh-ins, Google Health sync and chart)."""

from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from adamfit import auth, charts, google_health, google_health_connection, users, weights
from adamfit.ui import flash, show_flash
from adamfit.units import (
    cm_to_ft_in,
    from_display_weight,
    ft_in_to_cm,
    to_display_weight,
    weight_label,
)

UNIT_LABELS = {"imperial": "Pounds (lb, ft/in)", "metric": "Kilograms (kg, cm)"}
MAX_WEIGHT_KG = 699.0
# The Google login link is cached here, and remade before its 10-minute state expires
AUTH_URL_KEY = "google_health_auth_url"
AUTH_URL_MAX_AGE = timedelta(minutes=8)

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


@st.fragment
def show_weight_over_time(df: pd.DataFrame, key: str) -> None:
    """
    Draw the metrics, chart, chart controls and entries table for the weigh-ins.

    The controls and the chart come from ``charts.py``, shared with the Home
    page. The controls sit under the chart, but the metrics and the chart
    above them depend on them, so a container is reserved for those first
    and filled once the controls have been read. This is a fragment, so
    changing a control reruns only this section. It is also a function so
    it can ``return`` early when the chosen period has no weigh-ins.
    ``st.stop()`` would also cut off anything drawn after it on the page,
    which is fragile inside a tab.

    Parameters
    ----------
    df : pd.DataFrame
        All of the user's weigh-ins, oldest first, with a ``weight`` column
        already converted to the display unit. Must not be empty.
    key : str
        Prefix for the widget keys, passed in by ``charts.chart_card``.
    """
    metrics_and_chart = st.container()
    settings = charts.chart_controls(key, charts.WEIGHT_LINES)

    # Average over the full history first, so the start of the chart is accurate
    df = charts.add_rolling_average(df, "weigh_date", "weight", settings.window_days)
    view = charts.filter_dates(df, "weigh_date", settings.start, settings.end)

    with metrics_and_chart:
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
        col_avg.metric(f"{settings.window_days}-day average", f"{latest['rolling_avg']:.1f} {unit}")
        if len(view) > 1:
            col_change.metric(
                f"Change ({settings.period})",
                f"{view['weight'].iloc[-1] - view['weight'].iloc[0]:+.1f} {unit}",
            )
        charts.weight_chart(view, unit, settings)

    if view.empty:
        return

    with st.expander("Entries in this period"):
        entries = view[["weigh_date", "weight", "source"]].iloc[::-1]
        st.dataframe(
            entries.assign(source=entries["source"].map(weights.SOURCE_LABELS)),
            hide_index=True,
            column_config={
                "weigh_date": st.column_config.DateColumn("Date", format="MMM D, YYYY"),
                "weight": st.column_config.NumberColumn(f"Weight ({unit})", format="%.1f"),
                "source": st.column_config.TextColumn("Source"),
            },
        )


def connect_url() -> str:
    """
    Return the Google login link, making a new one only when needed.

    Making a link stores a fresh one-time state in the database, so it is
    kept in session state instead of being made on every rerun. It is
    remade after ``AUTH_URL_MAX_AGE``, a little before the state expires.

    Returns
    -------
    str
        The address of Google's consent page.
    """
    cached = st.session_state.get(AUTH_URL_KEY)
    if cached is None or datetime.now() - cached["created_at"] > AUTH_URL_MAX_AGE:
        cached = {"url": google_health.build_auth_url(user_id), "created_at": datetime.now()}
        st.session_state[AUTH_URL_KEY] = cached
    return cached["url"]


def show_google_health_sync() -> None:
    """
    Draw the Google Health sync section: setup hint, Connect button, or sync form.

    This is a function so it can ``return`` early for each connection state.
    """
    if not google_health.is_configured():
        st.caption(
            "Google Health isn't set up. Add the `GOOGLE_HEALTH_*` settings to `.env` "
            "as described in `docs/google_health_setup.md`, then restart the app."
        )
        return

    status = google_health_connection.get_status(user_id)
    if status is None or not status["is_connected"]:
        st.caption(
            "Connect once to copy weigh-ins from your Fitbit. Google opens in a new tab. "
            "When it says you're connected, close that tab, come back here and click "
            "**Refresh status**."
        )
        with st.container(horizontal=True):
            st.link_button(
                "Connect Google Health",
                connect_url(),
                icon=":material/link:",
                type="primary",
            )
            st.button("Refresh status", icon=":material/refresh:")
        return

    # Connected: the cached login link is no longer needed
    st.session_state.pop(AUTH_URL_KEY, None)
    last_synced = status["last_synced_at"]
    st.caption(
        f"Connected on {status['connected_at'].astimezone():%b %d, %Y}. "
        + (f"Last synced {last_synced.astimezone():%b %d, %Y at %H:%M}." if last_synced else "Not synced yet.")
    )

    with st.form("google_health_sync_form"):
        default_start = last_synced.astimezone().date() if last_synced else date.today() - timedelta(days=30)
        col_start, col_end = st.columns(2)
        start = col_start.date_input(
            "Start date", value=default_start, min_value=date(2010, 1, 1), max_value=date.today()
        )
        end = col_end.date_input(
            "End date", value=date.today(), min_value=date(2010, 1, 1), max_value=date.today()
        )
        st.caption(
            "Both dates are included. A synced weight replaces anything already stored for "
            "that day, including weights you typed in. If you weighed in more than once on a "
            "day, the latest one is kept."
        )
        submitted = st.form_submit_button("Sync now", icon=":material/sync:", type="primary")

    if submitted:
        if start > end:
            st.error("The start date must be on or before the end date.")
        else:
            try:
                with st.spinner("Fetching weigh-ins from Google Health..."):
                    summary = google_health.sync_weights(user_id, start, end)
            except google_health.NotConnectedError as exc:
                # The tokens were cleared, so rerun to show the Connect button
                flash(str(exc), kind="error")
                st.rerun()
            except google_health.GoogleHealthError as exc:
                st.error(str(exc))
            else:
                flash(
                    f"Synced {start:%b %d, %Y} to {end:%b %d, %Y}: "
                    f"{summary['weigh_ins']} weigh-in(s) found, {summary['days_saved']} day(s) saved."
                )
                st.rerun()

    if st.button("Disconnect", icon=":material/link_off:"):
        google_health.disconnect(user_id)
        flash("Google Health disconnected.")
        st.rerun()


# on_change="rerun" makes the tabs remember which one is open, and lets us
# run only the open tab's code
body_tab, weight_tab = st.tabs(["Body details", "Weight"], key="profile_tab", on_change="rerun")

# ---- Body details ------------------------------------------------------
if body_tab.open:
    with body_tab:
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

# ---- Weight ------------------------------------------------------------
if weight_tab.open:
    with weight_tab:
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

        with st.expander("Google Health sync", icon=":material/sync:"):
            show_google_health_sync()

        if df.empty:
            st.info("No weigh-ins yet. Log one above to see your charts.")
        else:
            # Each card has a Show toggle; a hidden card's code doesn't run
            charts.chart_card("Weight over time", "profile_weight", lambda key: show_weight_over_time(df, key))
            charts.chart_card(
                "Weight change",
                "profile_weight_change",
                lambda key: charts.show_weight_change(df, unit, key),
            )
