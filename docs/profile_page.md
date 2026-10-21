# My Profile Page

**File:** `src/adamfit/pages/profile.py`

## What you see
At the top of the page:
- **Units**: switch between pounds/feet-inches and kilograms/centimetres. The choice is saved to your profile. It sits above the tabs because it changes how both tabs show numbers.

Below that are two tabs:
1. **Body details**: sex, height and birth date, saved with one button.
2. **Weight**:
   - **Log weight**: pick a date and enter a weight. Entering a date that already has a weight replaces it. An expander lets you delete an entry.
   - **Google Health sync** (an expander): copies weigh-ins from your Fitbit through Google Health. It shows one of three things:
     - *Not set up*: a note pointing to [Google Health setup](google_health_setup.md) when the `GOOGLE_HEALTH_*` settings are missing from `.env`.
     - *Not connected*: a **Connect Google Health** button that opens Google in a new tab, and a **Refresh status** button to press when you come back.
     - *Connected*: when you connected and last synced, a start and end date (both included), **Sync now**, and **Disconnect**.
   - **Weight over time**: current weight, rolling average and change for the chosen period, a line chart of weigh-ins plus the rolling average, and a table of the entries with where each came from (**Manual** or **Fitbit**).

## How it works
1. The logged-in user is loaded, and their unit preference decides how everything on the page is shown. The database always stores kilograms and centimetres. Conversion happens only for display (see `src/adamfit/units.py`).
   ```python
   user = auth.current_user()
   unit_system = user["unit_system"]
   unit = weight_label(unit_system)   # "lb" or "kg"
   ```
2. **Units toggle.** Changing it calls `save_unit_system` *before* the page reruns (an `on_change` callback), so the rerun already uses the new unit.
   ```python
   st.segmented_control(
       "Units",
       options=list(UNIT_LABELS),
       format_func=UNIT_LABELS.get,
       default=unit_system,
       required=True,
       key="unit_choice",
       on_change=save_unit_system,
   )
   ```
3. **Tabs.** `on_change="rerun"` makes the tabs remember which one is open (so it stays open after a save), and lets the page run only the open tab's code. Weigh-ins are only loaded from the database when the Weight tab is open.
   ```python
   body_tab, weight_tab = st.tabs(["Body details", "Weight"], key="profile_tab", on_change="rerun")

   if body_tab.open:
       with body_tab:
           ...
   if weight_tab.open:
       with weight_tab:
           ...
   ```
4. **Body details form** (Body details tab). In imperial mode, height is entered as feet and inches and converted to centimetres before saving.
   ```python
   if st.form_submit_button("Save details"):
       if unit_system == "imperial":
           height_cm = ft_in_to_cm(feet or 0, inches or 0)
       else:
           height_cm = height_cm_input or 0
       users.update_profile(user_id, sex, round(height_cm, 1) or None, birth_date)
       flash("Body details saved.")
       st.rerun()
   ```
   `flash` stores the message so it survives the rerun, and `show_flash()` at the top of the page displays it.
5. **Log weight form** (Weight tab). The weight box starts with your latest weigh-in. Saving converts it to kilograms.
   ```python
   weights.save_weight(user_id, weigh_date, from_display_weight(weight, unit_system))
   ```
6. **Google Health sync.** `show_google_health_sync` returns early for each state. When not connected, the Google login link is made once and kept in `st.session_state`, because making one stores a new one-time "state" value in the database. It is remade after 8 minutes, before that value expires (10 minutes).
   ```python
   cached = st.session_state.get(AUTH_URL_KEY)
   if cached is None or datetime.now() - cached["created_at"] > AUTH_URL_MAX_AGE:
       cached = {"url": google_health.build_auth_url(user_id), "created_at": datetime.now()}
       st.session_state[AUTH_URL_KEY] = cached
   ```
   ```python
   with st.container(horizontal=True):
       st.link_button(
           "Connect Google Health",
           connect_url(),
           icon=":material/link:",
           type="primary",
       )
       st.button("Refresh status", icon=":material/refresh:")
   ```
   Google sends you back to the app in that new tab, which is a new, logged-out session. `app.py` finishes the connection there and the login page shows the result (see [How syncing works](google_health_setup.md#how-syncing-works)). **Refresh status** just reruns this tab so it sees the new connection.
7. **Syncing.** The two dates are in a form, so nothing happens until **Sync now**. A start after the end shows an error. Otherwise the sync runs under a spinner, and a summary is flashed. If the connection has expired, the error is flashed and the page reruns, showing the Connect button again.
   ```python
   try:
       with st.spinner("Fetching weigh-ins from Google Health..."):
           summary = google_health.sync_weights(user_id, start, end)
   except google_health.NotConnectedError as exc:
       # The tokens were cleared, so rerun to show the Connect button
       flash(str(exc), kind="error")
       st.rerun()
   except google_health.GoogleHealthError as exc:
       st.error(str(exc))
   ```
   The start date defaults to the day of the last sync (or 30 days ago), and the end date to today.
8. **Weight over time.** With no weigh-ins yet, an info box is shown instead of the chart. Otherwise `show_weight_over_time` draws the rest of the section.
   ```python
   st.subheader("Weight over time")
   if df.empty:
       st.info("No weigh-ins yet. Log one above to see your chart.")
   else:
       show_weight_over_time(df)
   ```
9. **Chart controls.** You pick a period (default 3 months) and a rolling-average window in days (default 7).
   ```python
   period = col_period.segmented_control("Time period", list(PERIODS), default="3M", required=True)
   window_days = col_window.number_input("Rolling average (days)", min_value=1, max_value=90, value=7, step=1)
   ```
10. **Rolling average.** It is calculated over your *whole* history first, then trimmed to the period. That way the first point on a 3-month chart still averages the days before it.
   ```python
   df = weights.add_rolling_average(df, "weight", window_days)
   view = df[df["weigh_date"] >= pd.Timestamp(date.today() - timedelta(days=days_back))]
   ```
11. **Metrics and chart.** Two Altair line charts (thin with dots for weigh-ins, thick for the average) are layered with `+`.
   ```python
   weigh_ins = base.transform_filter(alt.datum.series == "Weigh-in").mark_line(point=True, opacity=0.5)
   average = base.transform_filter(alt.datum.series == avg_label).mark_line(strokeWidth=3)
   st.altair_chart(weigh_ins + average)
   ```
   If the chosen period has no weigh-ins, an info box is shown and the function returns early, so no chart is drawn. A `return` is used instead of `st.stop()`, which would end the whole page run.

## Widgets used
- [st.title / st.subheader / st.caption](widgets/st_title.md): page and section headings, hints
- [st.segmented_control](widgets/st_segmented_control.md): units toggle (saved via `on_change`) and chart period
- [st.form / st.form_submit_button](widgets/st_form.md): body details, weight entry, and the sync dates
- [st.selectbox](widgets/st_selectbox.md): sex, and the date to delete
- [st.number_input](widgets/st_number_input.md): height, weight and rolling-average days
- [st.date_input](widgets/st_date_input.md): birth date, weigh-in date, and the sync start and end dates
- [st.button](widgets/st_button.md): delete an entry, Refresh status, and Disconnect
- [st.link_button](widgets/st_link_button.md): Connect Google Health, opening Google in a new tab
- [st.spinner](widgets/st_spinner.md): shown while weigh-ins are fetched from Google Health
- [st.metric](widgets/st_metric.md): current weight, average and change
- [st.altair_chart](widgets/st_altair_chart.md): the weight chart
- [st.dataframe](widgets/st_dataframe.md): entries table (date, weight, source), using `column_config`
- [st.tabs](widgets/st_tabs.md): the Body details and Weight tabs, running only the open one
- [st.columns / st.container / st.expander](widgets/st_layout.md): side-by-side inputs, the Connect / Refresh status row, and collapsible sections
- [st.success / st.error / st.info](widgets/st_status_messages.md): save and sync confirmations, Google Health errors, and empty-state notes

## Core functions
- `show_weight_over_time` (`src/adamfit/pages/profile.py`): draws the chart controls, metrics, chart and entries table for the weigh-ins.
  ```python
  show_weight_over_time(df)
  ```
- `show_google_health_sync` / `connect_url` (`src/adamfit/pages/profile.py`): draw the sync section, and make (or reuse) the Google login link.
- `is_configured`, `build_auth_url`, `sync_weights`, `disconnect` (`src/adamfit/google_health.py`): check `.env` has the settings, make a login link, download and save weigh-ins, and disconnect. Errors are `GoogleHealthError` subclasses with a message for the user.
  ```python
  summary = google_health.sync_weights(user_id, date(2026, 10, 1), date(2026, 10, 21))
  # {"weigh_ins": 25, "days_saved": 21}
  ```
- `get_status` (`src/adamfit/google_health_connection.py`): whether the user is connected, and when they connected and last synced. It never returns tokens.
- `current_user` (`src/adamfit/auth.py`): loads the logged-in user's profile.
- `update_unit_system` / `update_profile` (`src/adamfit/users.py`): save the unit choice and body details.
  ```python
  users.update_profile(user_id, "male", 177.8, date(1990, 5, 1))
  ```
- `get_weights` (`src/adamfit/weights.py`): loads all weigh-ins (date, kg, source) as a pandas table, oldest first. Only called when the Weight tab is open. `SOURCE_LABELS` turns the source into "Manual" or "Fitbit".
- `save_weight` (`src/adamfit/weights.py`): inserts a weigh-in, or replaces the one for that date (`ON CONFLICT ... DO UPDATE`), and marks it `manual`.
- `save_synced_weights` (`src/adamfit/weights.py`): saves synced weigh-ins (one per day) in one transaction, overwriting any stored value for those days and marking them `google_health`.
- `delete_weight` (`src/adamfit/weights.py`): removes the weigh-in for one date.
- `add_rolling_average` (`src/adamfit/weights.py`): adds a `rolling_avg` column averaging the last *N calendar days*, so skipped days are handled correctly.
  ```python
  df = weights.add_rolling_average(df, "weight", 7)
  ```
- `to_display_weight` / `from_display_weight`, `cm_to_ft_in` / `ft_in_to_cm` (`src/adamfit/units.py`): unit conversions.
- `flash` / `show_flash` (`src/adamfit/ui.py`): show a success (or, with `kind="error"`, an error) message after `st.rerun()`.

## Database tables used
- `app_user`: reads the profile, and updates `sex`, `height_cm`, `birth_date` and `unit_system`.
- `user_weight`: reads, inserts, updates and deletes weigh-ins. The `source` column records `manual` or `google_health`.
- `google_health_connection`: reads the connection status; stores the one-time login state; the sync reads and refreshes tokens and sets `last_synced_at`; Disconnect clears the tokens (the row is kept).
