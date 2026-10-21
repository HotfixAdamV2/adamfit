# Home Page

**File:** `src/adamfit/pages/home.py`

## What you see
A centred "Fitness Dashboard" title with today's date underneath. Below that is a row of boxed tiles with the total fat, carbs, protein, fiber and calories you have logged today. If you have not logged anything today, the tiles show zero and a short note points you to the Nutrition page. You only see this page after logging in.

## How it works
1. The page reads who is logged in and today's date.
   ```python
   user_id = st.session_state["user_id"]
   today = date.today()
   ```
2. It draws the centred title and a caption naming today's date.
   ```python
   st.title("Fitness Dashboard", text_alignment="center")
   st.caption(f"Today's macros · {today:%A, %b %d, %Y}", text_alignment="center")
   ```
3. It loads today's food log, scales each entry's macros to the amount eaten, and adds them up. An empty log adds up to zero.
   ```python
   log = food_logs.get_log(user_id, today)
   totals = totals_row(scale_entries(log)).iloc[0]
   ```
4. It shows one tile per macro, side by side, using `macro_tiles` from `ui.py`. Calories are whole numbers; grams have one decimal. The Nutrition page's Daily log uses the same helper, so the two look identical.
   ```python
   macro_tiles(totals)
   ```
   Inside `macro_tiles`:
   ```python
   with st.container(horizontal=True):
       for column, label in MACROS.items():
           value = float(totals[column])
           st.metric(label, f"{value:,.0f}" if column == "calories" else f"{value:.1f}", border=True)
   ```
5. If nothing was logged today, a note says so.
   ```python
   if log.empty:
       st.info("Nothing logged today yet. Add food on the Nutrition page.")
   ```

## Widgets used
- [st.title / st.caption](widgets/st_title.md): the centred title and today's date
- [st.container](widgets/st_layout.md): a horizontal row that holds the tiles (wraps on small screens)
- [st.metric](widgets/st_metric.md): one boxed tile per macro total
- [st.info](widgets/st_status_messages.md): the "nothing logged today" note

## Core functions
- `get_log` (`src/adamfit/food_logs.py`): loads everything the user logged on one day, with per-serving macros.
  ```python
  log = food_logs.get_log(user_id, today)
  ```
- `scale_entries` and `totals_row` (`src/adamfit/nutrition.py`): multiply each entry's macros by the servings eaten, then add them into a single "Total" row.
  ```python
  totals = totals_row(scale_entries(log)).iloc[0]
  ```
- `macro_tiles` (`src/adamfit/ui.py`): draws the row of boxed tiles, one per macro, from a totals row.
  ```python
  macro_tiles(totals)
  ```
- `MACROS` (`src/adamfit/nutrition.py`): the macro column names and their labels, in display order (fat, carbs, protein, fiber, calories). The tiles follow this list.
  ```python
  MACROS = {
      "fat_g": "Fat (g)",
      "carbs_g": "Carbs (g)",
      "protein_g": "Protein (g)",
      "fiber_g": "Fiber (g)",
      "calories": "Calories",
  }
  ```

## Database tables used
- `food_log`: read only (today's entries for the logged-in user).
- `food` and `vw_recipe_nutrition`: read only, joined by `get_log` for the macros of each food or recipe.
