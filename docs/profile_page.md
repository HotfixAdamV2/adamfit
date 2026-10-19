# My Profile Page

**File:** `src/adamfit/pages/profile.py`

## What you see
From top to bottom:
1. **Units**: switch between pounds/feet-inches and kilograms/centimetres. The choice is saved to your profile.
2. **Body details**: sex, height and birth date, saved with one button.
3. **Log weight**: pick a date and enter a weight. Entering a date that already has a weight replaces it. An expander lets you delete an entry.
4. **Weight over time**: current weight, rolling average and change for the chosen period, a line chart of weigh-ins plus the rolling average, and a table of the entries.

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
3. **Body details form.** In imperial mode, height is entered as feet and inches and converted to centimetres before saving.
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
4. **Log weight form.** The weight box starts with your latest weigh-in. Saving converts it to kilograms.
   ```python
   weights.save_weight(user_id, weigh_date, from_display_weight(weight, unit_system))
   ```
5. **Chart controls.** You pick a period (default 3 months) and a rolling-average window in days (default 7).
   ```python
   period = col_period.segmented_control("Time period", list(PERIODS), default="3M", required=True)
   window_days = col_window.number_input("Rolling average (days)", min_value=1, max_value=90, value=7, step=1)
   ```
6. **Rolling average.** It is calculated over your *whole* history first, then trimmed to the period. That way the first point on a 3-month chart still averages the days before it.
   ```python
   df = weights.add_rolling_average(df, "weight", window_days)
   view = df[df["weigh_date"] >= pd.Timestamp(date.today() - timedelta(days=days_back))]
   ```
7. **Metrics and chart.** Two Altair line charts (thin with dots for weigh-ins, thick for the average) are layered with `+`.
   ```python
   weigh_ins = base.transform_filter(alt.datum.series == "Weigh-in").mark_line(point=True, opacity=0.5)
   average = base.transform_filter(alt.datum.series == avg_label).mark_line(strokeWidth=3)
   st.altair_chart(weigh_ins + average)
   ```
   If there are no weigh-ins, an info box is shown and `st.stop()` ends the page early.

## Widgets used
- [st.title / st.subheader / st.caption](widgets/st_title.md): page and section headings, hints
- [st.segmented_control](widgets/st_segmented_control.md): units toggle (saved via `on_change`) and chart period
- [st.form / st.form_submit_button](widgets/st_form.md): body details and weight entry
- [st.selectbox](widgets/st_selectbox.md): sex, and the date to delete
- [st.number_input](widgets/st_number_input.md): height, weight and rolling-average days
- [st.date_input](widgets/st_date_input.md): birth date and weigh-in date
- [st.button](widgets/st_button.md): delete an entry
- [st.metric](widgets/st_metric.md): current weight, average and change
- [st.altair_chart](widgets/st_altair_chart.md): the weight chart
- [st.dataframe](widgets/st_dataframe.md): entries table, using `column_config`
- [st.columns / st.expander](widgets/st_layout.md): side-by-side inputs, and collapsible sections
- [st.success / st.info](widgets/st_status_messages.md): save confirmations and empty-state notes

## Core functions
- `current_user` (`src/adamfit/auth.py`): loads the logged-in user's profile.
- `update_unit_system` / `update_profile` (`src/adamfit/users.py`): save the unit choice and body details.
  ```python
  users.update_profile(user_id, "male", 177.8, date(1990, 5, 1))
  ```
- `get_weights` (`src/adamfit/weights.py`): loads all weigh-ins as a pandas table, oldest first.
- `save_weight` (`src/adamfit/weights.py`): inserts a weigh-in, or replaces the one for that date (`ON CONFLICT ... DO UPDATE`).
- `delete_weight` (`src/adamfit/weights.py`): removes the weigh-in for one date.
- `add_rolling_average` (`src/adamfit/weights.py`): adds a `rolling_avg` column averaging the last *N calendar days*, so skipped days are handled correctly.
  ```python
  df = weights.add_rolling_average(df, "weight", 7)
  ```
- `to_display_weight` / `from_display_weight`, `cm_to_ft_in` / `ft_in_to_cm` (`src/adamfit/units.py`): unit conversions.
- `flash` / `show_flash` (`src/adamfit/ui.py`): show a success message after `st.rerun()`.

## Database tables used
- `app_user`: reads the profile, and updates `sex`, `height_cm`, `birth_date` and `unit_system`.
- `user_weight`: reads, inserts, updates and deletes weigh-ins.
