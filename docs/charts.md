# Charts over time (shared)

**File:** `src/adamfit/charts.py`

The charts are written once in `charts.py` and used on several pages:

| Chart | Used on |
|-------|---------|
| Weight over time | [Home page](home_page.md), [My Profile page](profile_page.md) (Weight tab, with extra metrics and an entries table) |
| Weight change | [Home page](home_page.md), [My Profile page](profile_page.md) (Weight tab, under the weight chart) |
| Calories and macros over time | [Home page](home_page.md), [Nutrition page](nutrition_page.md) (Daily log tab) |

## What you see
Every chart sits in a bordered **card**: its name, a **Show** switch, then the chart, then its controls underneath. Turn **Show** off to fold the card down to its heading. The switch, and every control, remembers its setting for the rest of your session, even after visiting other pages.

The controls, stacked so they fit in half a page:
- **Time period**: 1M, 3M (the default), 6M, 1Y, All or **Custom**. Custom shows a **Date range** calendar where you click a start day, then an end day. Until you click the end day, the chart shows from the start day up to today, with a note saying so.
- **Rolling average (days)**: how many calendar days the average covers (1 to 90, default 7).
- **Lines** (line charts): pills to turn the thin line (weigh-ins, or daily totals) and the bold average line on or off.
- The macros chart also has **Show**: fat, carbs, protein, fiber or calories (the default).
- The weight change chart has **Compare** (Daily, Weekly or Monthly, default Weekly), **Chart** (Bars, the default, or Lines), a **% change** switch (on at first), and **Based on** instead of Lines: the weigh-ins, the rolling average (the default), or both.

**Hovering a line chart** shows a grey line at the nearest date, a dot on each visible line, and one tooltip with the date, that day's value (weigh-in or daily total) and the N-day average. The tooltip always shows both values, even when one line is turned off: hiding a line tidies the picture, but the exact numbers stay one hover away. A missing value shows as "–".

**The weight change chart** shows one value per day, week (Monday to Sunday) or calendar month, in your units (lb or kg) on the left axis:
- **Bars**: orange for a gain, blue for a loss, with a grey line at zero. Neither colour means "good": that depends on your goal. With both sources on, each period has two bars side by side, and the weigh-in bar is paler.
- **Lines**: one solid line per source, grey for weigh-ins and blue for the average, the same colours as the weight chart.

With **% change** on, the percentage change is added as **dashed light green** lines on a right-hand axis, "Change (%)". The legend shows solid = lb/kg and dashed = %. Zero is at the same height on both axes, so a bar or point above the grey zero line is a gain on both. Because each % is the change divided by a weight that hardly moves from week to week, the dashed lines usually sit close to the solid ones: the right axis is there so you can read off the %.

Hovering picks the nearest period: a grey line marks it, and one tooltip lists, for every source shown, the change and the % (e.g. "-1.2 lb (-0.8%)") and the weight at the end of the period, plus the date that value comes from.

Dates on the x axes and in the tooltips are written `YYYY-MM-DD`.

## How it works
1. **Cards and key prefixes.** `chart_card` draws the border, the heading and the Show switch, then calls the chart's draw function with a key prefix. Every widget key starts with that prefix, so the same chart can be on two pages without two widgets sharing a key. When Show is off, the draw function is not called at all, so a hidden chart runs no database queries.
   ```python
   with st.container(border=True, height="stretch" if stretch else "content"):
       with st.container(horizontal=True, vertical_alignment="center"):
           st.subheader(title)
           shown = st.toggle("Show", value=True, key=f"{key}_shown", persist_state=PERSIST)
       if shown:
           draw(key)
   ```
   `PERSIST` is `"session"`. Every chart widget uses `persist_state=PERSIST`, which keeps its value while the card is hidden and when you switch pages.
2. **The dashboard grid.** `chart_grid` takes a list of `Card`s and lays them out two per row with `st.columns(2)`. An odd last card sits on the left. To add a chart to the Home page, add a `Card` to the list.
   ```python
   for first in range(0, len(cards), 2):
       columns = st.columns(2)
       for column, card in zip(columns, cards[first : first + 2]):
           with column:
               chart_card(card.title, card.key, card.draw, stretch=True)
   ```
3. **Lining up cards in a row.** Cards have different controls (the macros chart has an extra macro picker, a custom range adds a date picker), so controls *above* the chart would push the plots to different heights. Instead, every card draws its plot straight under the heading, at the same fixed `CHART_HEIGHT` (300 pixels), with the controls underneath. Each heading row is the same, so the plots line up top and bottom whatever the controls are. `stretch=True` (`height="stretch"`) also makes the two borders in a row equally tall. The controls are read first, so the chart's spot is reserved with an empty `st.container()` and filled afterwards:
   ```python
   plot = st.container()
   settings = chart_controls(key, WEIGHT_LINES)
   averaged = add_rolling_average(weigh_ins, "weigh_date", "weight", settings.window_days)
   with plot:
       weight_chart(filter_dates(averaged, "weigh_date", settings.start, settings.end), unit, settings)
   ```
   (A spacer that pushes the plot to the bottom of the card doesn't work here: each chart is a fragment, and a fragment wraps its content in its own container, which only grows to fit its content.)
4. **Half-picked date range.** A date range picker returns a single date while you are halfway through picking, so that case is handled on its own:
   ```python
   if len(picked) == 2:
       return period, picked[0], picked[1]
   if len(picked) == 1:
       st.caption("Pick an end date. Showing up to today for now.")
       return period, picked[0], today
   return period, None, today
   ```
5. **Average first, then trim.** The rolling average is worked out on the whole history before cutting the rows down to the chosen dates, so the first point on a 3-month chart still averages the days before it. The macros chart loads only the days it needs: the chosen range plus `window_days` before it.
   ```python
   load_from = None if settings.start is None else settings.start - timedelta(days=settings.window_days)
   totals = food_logs.get_daily_totals(user_id, load_from, settings.end)
   ```
6. **Days with nothing logged are skipped.** `get_daily_totals` only returns days that have log entries. A day you didn't log is not a day you ate nothing, so it is not counted as zero. The rolling average is the mean of the *logged* days in the window. Weigh-ins work the same way.
7. **One macro at a time.** Calories run into the thousands while grams are in the tens, so on one shared axis the gram lines would be flat along the bottom. Showing one macro at a time keeps one readable y axis.
8. **The hover tooltip.** This is Altair's multi-line tooltip pattern. A *nearest point selection* on the date follows the pointer. `empty=False` means nothing is selected until the pointer is over the chart.
   ```python
   hover = alt.selection_point(
       nearest=True, on="pointerover", clear="pointerout", fields=[date_column], empty=False
   )
   ```
   The lines are drawn from *long* data (one row per date and line). The tooltip comes from *wide* data (one row per date, with both values already written as text such as `"160.4 lb"`). That wide data feeds a layer of invisible vertical rules that hold the selection and the tooltip. The hovered rule turns grey, and a dot appears on each visible line at that date:
   ```python
   alt.Chart(wide)
   .mark_rule(color="gray", strokeWidth=1)
   .encode(
       x=x,
       opacity=alt.condition(hover, alt.value(0.6), alt.value(0)),
       tooltip=[
           alt.Tooltip(f"{date_column}:T", title="Date", format=DATE_FORMAT),
           alt.Tooltip("raw_text:N", title=raw_label),
           alt.Tooltip("avg_text:N", title=avg_label),
       ],
   )
   .add_params(hover)
   ```
   Missing values are dropped from the line data, so they can't break a line, and show as "–" in the tooltip.
9. **Weight change maths.** `period_changes` groups the days into periods (pandas `to_period`: `"D"` day, `"W"` Monday-to-Sunday week, `"M"` calendar month). It takes each period's **last** value: the last weigh-in, or the rolling average on the last date that has one (worked out on the full history first). The change is that value minus the previous period's value, and the % change is the change as a percentage of the previous period's value:
   ```python
   period_start = data[date_column].dt.to_period(freq).dt.start_time
   last_rows = data.groupby(period_start).last()
   ...
   out["previous"] = out["value"].shift(1)
   out["change"] = out["value"] - out["previous"]
   # A previous value of 0 would divide by zero, so it gives NaN instead
   out["pct"] = out["change"] / out["previous"].where(out["previous"] != 0) * 100
   ```
   For example, 98.0 lb one week and 97.0 lb the next is a change of -1.0 lb, and -1.0 / 98.0 × 100 = -1.02%.

   **Gaps:** periods with no weigh-ins are skipped. The next period with data is compared with the last period *before* the gap, for both the change and the %. So a value after a gap can cover more than one period's change. The tooltip shows the date the period-end value comes from. The first period in your history has nothing to compare with, so it is left out. A chosen range that starts mid-week (or mid-month) still includes that whole period. Data after the range's end date is ignored.
10. **Two y axes with zero lined up.** The left axis (lb or kg) and the right axis (%) each have their own scale (`resolve_scale(y="independent")`). The left layers (bars or solid lines, plus the single zero rule) form one group and the % lines another, so each group shares one axis. Left to themselves, the two zeros would sit at different heights, so `aligned_domains` sets both ranges by hand. The left range `[lo, hi]` always includes 0 (with 10% padding), and the right range is the same range times one factor `k`: `[lo × k, hi × k]`. Multiplying both ends by the same number keeps 0 at the same height.
   ```python
   lo = min(float(change.min()), 0.0)
   hi = max(float(change.max()), 0.0)
   span = (hi - lo) or 1.0  # all zero: still draw a small range around 0
   lo -= 0.1 * span
   hi += 0.1 * span

   pct = pct.dropna()
   k = 0.0
   if not pct.empty:
       # lo < 0 < hi after padding, so neither division is by zero
       k = max(float(pct.max()) / hi, float(pct.min()) / lo)
   if not k > 0:  # also catches NaN
       k = 1.0
   # 10% headroom, so the biggest % doesn't sit right on the axis edge
   k *= 1.1
   return [lo, hi], [lo * k, hi * k]
   ```
   `k` is worked out separately for the top and the bottom, and the bigger one is used. A single `max|pct| / max|change|` can cut off a value on the other side, because each % is divided by a different previous weight. With no % values, or all changes zero, `k` falls back to 1, so nothing is ever divided by zero. The right axis is formatted `+.1%`. That format multiplies by 100, so the chart plots `pct / 100`.
   ```python
   axis=alt.Axis(orient="right", format="+.1%"),
   ```
   The dash pattern is a `strokeDash` encoding on a small `measure` field ("Change (lb)" or "Change (%)") added to each layer, so solid and dashed get their own legend. The dots are drawn as separate layers: dots on the line itself would make Vega-Lite hide the legend's line symbols.
11. **Bars or lines, and the hover.** The x axis uses the period start as `YYYY-MM-DD` text. In **Bars** mode, colour means gain or loss (fixed colours), and two sources sit side by side (`xOffset`), the weigh-in bar paler. In **Lines** mode, colour means the source (grey weigh-ins, blue average) for the solid lines. In both modes the dashed % lines are light green (`PCT_LINE_COLOR`), paler for weigh-ins when both sources are on, and the right axis title is green too, so the % lines never blend into the blue ones:
   ```python
   "color": alt.Color(
       "direction:N",
       title=None,
       scale=alt.Scale(domain=["Gain", "Loss"], range=[GAIN_COLOR, LOSS_COLOR]),
       legend=alt.Legend(orient="bottom"),
   ),
   ```
   In both modes the hover works like the line charts. A nearest point selection on `period_label`, and a layer of invisible rules (one per period, built from one-row-per-period data with a column per source), show one tooltip for the whole period.
12. **Date axis.** Line charts use the `YYYY-MM-DD` format, hide labels that would overlap, and pick a tick step (day, week, month...) from how many days are shown (`date_ticks`). Without a step, a short range can get several ticks per day, all with the same label.
13. **Fragments.** `show_weight_over_time`, `show_weight_change` and `show_macros_over_time` are `@st.fragment`s, so changing a chart's control reruns only that chart. The Show switch is outside the fragment, so flipping it reruns the page.

## Widgets used
- [st.toggle](widgets/st_toggle.md): the Show switch on each card, and the weight change chart's % change switch
- [st.segmented_control](widgets/st_segmented_control.md): the time period, which macro to show, Daily / Weekly / Monthly, and Bars / Lines
- [st.date_input](widgets/st_date_input.md): the custom date range (a `(start, end)` pair)
- [st.number_input](widgets/st_number_input.md): the rolling-average window
- [st.pills](widgets/st_pills.md): which lines to show, or which source the weight change is based on (`selection_mode="multi"`)
- [st.altair_chart](widgets/st_altair_chart.md): the charts, at a fixed `height`
- [st.columns / st.container](widgets/st_layout.md): the two-wide grid, the bordered cards, the heading row, the reserved chart spot, and the row holding the window box and the pills
- [st.subheader / st.caption](widgets/st_title.md): card headings, and the note shown while a custom range is half picked
- [st.info](widgets/st_status_messages.md): empty-chart notes (no data, no data in the period, nothing chosen)
- [st.fragment](widgets/st_fragment.md): reruns only the chart when one of its controls changes

## Core functions
- `chart_card` / `chart_grid` / `Card` (`src/adamfit/charts.py`): a card with a Show switch, and a two-wide grid of cards.
  ```python
  charts.chart_card("Macros over time", "nutrition_macros", lambda key: charts.show_macros_over_time(user_id, key))
  ```
- `chart_controls` (`src/adamfit/charts.py`): draws the controls and returns a `ChartSettings` (`period`, `start`, `end`, `window_days`, `lines`). `default_lines` and `lines_label` let the weight change chart start with only the average, under the label "Based on".
- `add_rolling_average` (`src/adamfit/charts.py`): adds a `rolling_avg` column averaging the last *N calendar days*. The date column is a parameter, so it works for weigh-ins and log days.
  ```python
  df = charts.add_rolling_average(df, "weigh_date", "weight", 7)
  ```
- `filter_dates` (`src/adamfit/charts.py`): keeps the rows between two dates (a start of None means no start).
- `period_changes` (`src/adamfit/charts.py`): the period-end value, the previous period's value, the change and the % change, compared with the previous period with data.
  ```python
  changes = charts.period_changes(averaged, "weigh_date", "rolling_avg", "W", start, date.today())
  ```
- `aligned_domains` (`src/adamfit/charts.py`): y ranges for the change and % axes, with 0 at the same height on both.
  ```python
  left_domain, right_domain = aligned_domains(data["change"], data["pct"])
  ```
- `time_series_chart` / `weight_chart` / `weight_change_chart` (`src/adamfit/charts.py`): draw the Altair charts. `weight_change_chart` takes the chart type (`"Bars"` or `"Lines"`) and whether to show the % axis.
- `show_weight_over_time` / `show_weight_change` / `show_macros_over_time` (`src/adamfit/charts.py`): ready-made chart sections with their controls, for use inside a card.
- `get_daily_totals` (`src/adamfit/food_logs.py`): one row per logged day with the summed macros. Each entry's per-serving macros (from `food`, or `vw_recipe_nutrition` for recipes) are multiplied by its servings.

## Database tables used
- `user_weight`: read (through `weights.get_weights`, called by the page).
- `food_log`, `food` and `vw_recipe_nutrition`: read by `get_daily_totals`, only while the macros card is shown.
