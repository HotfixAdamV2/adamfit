# Home Page

**File:** `src/adamfit/pages/home.py`

## What you see
A centred "Fitness Dashboard" title with today's date underneath. Then:
- **Today's weight**, in your units (lb or kg). If you haven't weighed in today, a yellow reminder appears instead, with a link to the My Profile page where you log it (on the Weight tab).
- A row of boxed tiles with the total fat, carbs, protein, fiber and calories you have logged today. If you have not logged anything today, the tiles show zero and a short note points you to the Nutrition page.
- A grid of chart cards, always two wide:
  - **Weight over time**: your weigh-ins and their rolling average.
  - **Calories and macros over time**: calories per day (or fat, carbs, protein or fiber) and their rolling average.
  - **Weight change** (next row, on the left): how much you gained or lost per week (or day, or month), as bars or lines, with the % change on a right-hand axis (switch it off with **% change**).

All charts default to the last 3 months and a 7-day average. You can pick another period or your own dates and change the average window. On the line charts you can turn either line off and hover to see both values for a day. Each card has a **Show** switch to fold it away; a folded card makes its row shorter. Cards in the same row have their charts at the same height, so the plots line up. See [Charts over time](charts.md) for how the controls work. If you have no weigh-ins, or nothing logged in the period, a note is shown instead of the chart.

You only see this page after logging in.

## How it works
1. The page loads the logged-in user and works out their weight unit.
   ```python
   user = auth.current_user()
   user_id = user["user_id"]
   unit = weight_label(user["unit_system"])
   today = date.today()
   ```
2. It loads all weigh-ins, converts them to the user's unit (the database stores kilograms), and looks for one dated today.
   ```python
   weigh_ins = weights.get_weights(user_id)
   weigh_ins["weight"] = weigh_ins["weight_kg"].map(lambda kg: to_display_weight(kg, user["unit_system"]))
   todays = weigh_ins[weigh_ins["weigh_date"] == pd.Timestamp(today)]
   ```
3. With no weigh-in today it shows a reminder and a link to My Profile. The link's path must match the one given to `st.Page` in `app.py`. Otherwise it shows today's weight in a boxed tile.
   ```python
   if todays.empty:
       with st.container(border=True):
           st.warning("You haven't logged your weight today.", icon=":material/monitor_weight:")
           # The path must match the one registered with st.Page in app.py
           st.page_link("pages/profile.py", label="Log it on My Profile (Weight tab)", icon=":material/person:")
   else:
       st.metric("Today's weight", f"{todays['weight'].iloc[0]:.1f} {unit}", border=True, width="content")
   ```
4. It loads today's food log, scales each entry's macros to the amount eaten, adds them up and shows one tile per macro with `macro_tiles` (shared with the Nutrition page). An empty log adds up to zero, and a note says so.
   ```python
   log = food_logs.get_log(user_id, today)
   totals = totals_row(scale_entries(log)).iloc[0]

   macro_tiles(totals)

   if log.empty:
       st.info("Nothing logged today yet. Add food on the Nutrition page.")
   ```
5. It lays out the chart cards with `chart_grid` from `charts.py`, two per row. Each `Card` has a title, a key prefix (keeping its widgets apart from the others and from other pages) and a function that draws the chart. A hidden card's function isn't called, so its query doesn't run.
   ```python
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
   ```
   To add a chart to the dashboard, add another `Card` to the list. Each chart is a fragment, so changing its controls reruns only that chart.

## Widgets used
- [st.title / st.subheader / st.caption](widgets/st_title.md): the centred title, today's date and the chart headings
- [st.warning / st.info](widgets/st_status_messages.md): the weigh-in reminder and the "nothing logged today" note
- [st.page_link](widgets/st_navigation.md): the link to My Profile from the weigh-in reminder
- [st.metric](widgets/st_metric.md): today's weight, and one boxed tile per macro total
- [st.columns / st.container](widgets/st_layout.md): the two-wide chart grid, bordered cards, and the horizontal row of tiles
- [st.toggle](widgets/st_toggle.md): the Show switch on each chart card, and the weight change chart's % change switch
- [st.segmented_control](widgets/st_segmented_control.md), [st.date_input](widgets/st_date_input.md), [st.number_input](widgets/st_number_input.md), [st.pills](widgets/st_pills.md), [st.altair_chart](widgets/st_altair_chart.md), [st.fragment](widgets/st_fragment.md): the chart controls and charts (see [Charts over time](charts.md))

## Core functions
- `current_user` (`src/adamfit/auth.py`): loads the logged-in user's profile, including `unit_system`.
- `get_weights` (`src/adamfit/weights.py`): loads every weigh-in, oldest first.
  ```python
  weigh_ins = weights.get_weights(user_id)
  ```
- `weight_label` / `to_display_weight` (`src/adamfit/units.py`): the unit name ("lb" or "kg") and the kilogram-to-display conversion.
- `get_log` (`src/adamfit/food_logs.py`): loads everything the user logged on one day, with per-serving macros.
- `scale_entries` and `totals_row` (`src/adamfit/nutrition.py`): multiply each entry's macros by the servings eaten, then add them into a single "Total" row.
- `macro_tiles` (`src/adamfit/ui.py`): draws the row of boxed tiles, one per macro, in the order of `MACROS` (fat, carbs, protein, fiber, calories).
- `chart_grid` / `Card` (`src/adamfit/charts.py`): the two-wide grid of chart cards, each with a Show switch.
- `show_weight_over_time` / `show_macros_over_time` / `show_weight_change` (`src/adamfit/charts.py`): the charts with their controls. See [Charts over time](charts.md).

## Database tables used
- `user_weight`: read only (all of the user's weigh-ins).
- `food_log`: read only (today's entries, and the daily totals for the macros chart while it is shown).
- `food` and `vw_recipe_nutrition`: read only, joined for the macros of each food or recipe.
