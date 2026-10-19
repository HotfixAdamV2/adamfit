# Nutrition Page

**File:** `src/adamfit/pages/nutrition.py`

## What you see
Three tabs:
1. **Daily log**: pick a day (with ‹ and › buttons for the previous and next day). Narrow the list with the **Category** and **Sub-category** boxes, search for a food or recipe, enter how many servings you ate and press **Add**. Recipes have their own "Recipes" entry in Category. A small note next to the box shows what one serving is (e.g. "1 serving = 30 g"). The table lists everything for that day with its servings, the amount those servings come to (e.g. "45 g"), then fat, carbs, protein, fiber and calories. Change the servings, or select rows and press Delete. The day's totals sit underneath as a row of boxed tiles, the same as on the Home page.
2. **Recipes**: choose a recipe or create one with **New recipe** (name, how many servings it makes, and what one serving is called, e.g. "bowl"). You see its macros per serving, an ingredients table that works like the daily log (with the same filters, foods only, and the whole-recipe **Total** row under the table), and the instructions. **Edit recipe details** changes the name, yield and instructions, or deletes the recipe. These save straight away.
3. **Foods**: your own food list, filterable by category and searchable by name. Edit any cell, add a food in the empty bottom row, or select rows and press Delete. Nothing is saved until you press **Save changes**.

**Nothing in the Daily log or the ingredients table is saved until you press Save changes.** Adds, servings changes and deletes show in the table and the totals straight away, and a note says how many are unsaved (e.g. "3 unsaved changes"). **Save changes** writes them all at once. **Revert changes** throws them away. Both buttons are greyed out when there is nothing to save. Unsaved changes belong to the day (or recipe) they were made on: moving to another day keeps them, and a yellow note lists the other days that still have unsaved changes. They are lost if you close the browser tab.

Amounts are always shown in the food's own serving unit (g, oz, cup, tbsp, bar...), exactly as it is set in the Foods tab. Two servings of a 4 oz steak show as 8 oz, whatever your unit setting. The imperial/metric choice on the Profile page only affects body weight, not foods. Recipes use their own serving label (e.g. 1.5 bowl).

## How it works
1. **One serving per food.** Every food has one serving (e.g. 4 oz, or 1 tbsp) and its macros are for that serving. The log and recipes store a *number of servings*. `nutrition.py` turns them into the amount you see, with no unit conversion: the amount is simply servings × serving size, in the food's own unit.
   ```python
   def to_amount(servings: float, serving_size: float) -> float:
       return servings * serving_size
   ```
2. **Macro order.** Every table and row of tiles follows the `MACROS` dictionary. Queries name their columns and rows are read by column name, so changing this order only changes the display.
   ```python
   MACROS = {
       "fat_g": "Fat (g)",
       "carbs_g": "Carbs (g)",
       "protein_g": "Protein (g)",
       "fiber_g": "Fiber (g)",
       "calories": "Calories",
   }
   ```
3. **Tabs that remember where you are.** `on_change="rerun"` makes the tabs track which one is open, and only that tab's code runs.
   ```python
   log_tab, recipe_tab, food_tab = st.tabs(
       ["Daily log", "Recipes", "Foods"], key="nutrition_tab", on_change="rerun"
   )
   ```
4. **Picker options carry their category.** Each food option has its parent category and sub-category. Recipes have no category in the database, so the page gives them the category "Recipes" and no sub-category. Options also carry the item's name and macros, so a staged add can be shown before it is saved.
   ```python
   "category": "Recipes",
   "sub_category": None,
   ```
5. **Filtering the add row.** `item_picker` (in `ui.py`) builds the Category list from the options, so it only shows categories that have items (and "Recipes" only where recipes are offered). Sub-category is greyed out until a category is picked, and picking a new category resets it to All. If the chosen item is filtered out, the item box is cleared. A widget's value can only be changed before it is drawn, so these resets happen just before each box.
   ```python
   visible = [
       option_key
       for option_key, option in options.items()
       if category in ("All", option["category"]) and sub_category in ("All", option["sub_category"])
   ]
   if st.session_state.get(item_key) is not None and st.session_state[item_key] not in visible:
       st.session_state[item_key] = None
   ```
6. **Staging changes.** The page keeps a "changes" dictionary in `st.session_state`, one per day (`log_changes_2026-10-19`) or per recipe (`recipe_changes_12`). Add, servings edits and deletes only change that dictionary. A staged add has no database id yet, so it gets a temporary negative id (-1, -2...). Deleting a staged add just forgets it.
   ```python
   changes_key = f"log_changes_{log_date.isoformat()}"
   changes = pending_changes(changes_key)
   ...
   on_add=lambda option_key, servings: stage_add(changes, option_key, servings),
   ```
7. **Showing the staged result.** `apply_changes` takes the rows from the database, drops the deleted ones, applies the edited servings and adds a row for each staged add. The editor, the totals and (on the Recipes tab) the per-serving tiles are all drawn from that.
   ```python
   log = apply_changes(food_logs.get_log(user_id, log_date), changes, options)
   ```
8. **The editor hands changes over straight away.** `entries_editor` (in `ui.py`) shows a `st.data_editor` where only Servings can be changed. Its `on_change` callback passes each edit or delete to the page's `stage_update` / `stage_delete`, then bumps a version number in the key. The new key gives a fresh editor, drawn from the staged rows.
   ```python
   on_update=lambda entry_id, servings: stage_update(changes, entry_id, servings),
   on_delete=lambda entry_id: stage_delete(changes, entry_id),
   ```
9. **Save and Revert.** `save_bar` (in `ui.py`) draws the two buttons and the "3 unsaved changes" note. Revert removes the changes dictionary. Save turns the staged adds into food or recipe ids and calls one save function, which writes everything in a single transaction: either all changes are saved or none are. Then the staged changes are cleared.
   ```python
   if save_bar(changes_key):
       ...
       food_logs.save_log_changes(user_id, log_date, adds, changes["updates"], changes["deletes"])
   ```
10. **The totals.** The Daily log passes `totals_as_tiles=True`, which shows them with `macro_tiles`, the same boxed tiles as the Home page. The Recipes tab keeps a one-row `st.dataframe` lined up with the ingredient columns, because the tiles above it already show the per-serving macros.
11. **Recipe macros are calculated, not typed.** In the database the `vw_recipe_nutrition` view adds up the ingredients. On screen the page does the same sum from the staged ingredients (so unsaved changes show), then divides by the recipe's yield.
    ```python
    totals = totals_row(scale_entries(ingredients)).iloc[0]
    ...
    per_serving = total / servings_per_recipe
    ```
12. **Selecting a new recipe.** After creating (or deleting) a recipe, the page stores the choice in `pending_recipe_choice` and applies it on the next run, just before the selectbox.
13. **Saving the food list.** The Foods editor sits inside a form, so edits are batched. On **Save changes**, the added, edited and deleted rows are saved in one transaction.
    ```python
    foods.save_food_changes(user_id, changes["added_rows"], updates, deletes)
    ```
14. **Deleting is a soft delete.** Removing a food or recipe sets `is_active = FALSE`. It disappears from your lists, but recipes and past days that used it keep their numbers. Log entries and ingredients are really deleted.

## Widgets used
- [st.tabs](widgets/st_tabs.md): the Daily log, Recipes and Foods tabs
- [st.data_editor](widgets/st_data_editor.md): the editable log, ingredient and food tables
- [st.dataframe](widgets/st_dataframe.md): the Total row under a recipe's ingredients table
- [st.selectbox](widgets/st_selectbox.md): the Category and Sub-category filters, picking a food, recipe or category
- [st.number_input](widgets/st_number_input.md): servings to add, and a recipe's number of servings
- [st.date_input](widgets/st_date_input.md): the day being logged
- [st.button](widgets/st_button.md): Add, previous/next day, Save changes, Revert changes and confirming a delete
- [st.text_input](widgets/st_text_input.md): recipe name, serving label and food search
- [st.text_area](widgets/st_text_area.md): recipe instructions
- [st.markdown](widgets/st_markdown.md): shows the instructions and small bold headings
- [st.metric](widgets/st_metric.md): the day's totals in the Daily log, and a recipe's macros per serving
- [st.form / st.form_submit_button](widgets/st_form.md): new recipe, recipe details and the food list
- [st.popover](widgets/st_popover.md): the New recipe form and the delete confirmation
- [st.container / st.columns / st.expander](widgets/st_layout.md): the filter, add and save rows, and the Edit recipe details section
- [st.title / st.subheader / st.caption](widgets/st_title.md): headings, hints, the "1 serving = ..." note and the unsaved-changes count
- [st.info / st.warning / st.error / st.success](widgets/st_status_messages.md): empty states, unsaved changes on other days, errors and save messages

## Core functions
- `get_log`, `save_log_changes` (`src/adamfit/food_logs.py`): read one day's log, and save a batch of adds, servings changes and deletes in one transaction. Raises `ValueError` if a number is too large.
  ```python
  food_logs.save_log_changes(user_id, log_date, adds, changes["updates"], changes["deletes"])
  ```
- `get_recipes`, `get_recipe`, `create_recipe`, `update_recipe`, `delete_recipe` (`src/adamfit/recipes.py`): manage recipes. Create and update raise `ValueError` if the name is taken.
  ```python
  recipe = recipes.get_recipe(user_id, recipe_id)
  ```
- `get_ingredients`, `save_ingredient_changes` (`src/adamfit/recipes.py`): read a recipe's ingredients, and save a batch of changes to them in one transaction.
  ```python
  recipes.save_ingredient_changes(
      user_id, recipe_id, adds, changes["updates"], changes["deletes"]
  )
  ```
- `get_foods`, `get_categories`, `get_serving_units`, `save_food_changes` (`src/adamfit/foods.py`): read and save the food list. `get_foods` also returns each food's parent and sub-category names for the filters. Categories and units are cached for an hour.
  ```python
  food_list = foods.get_foods(user_id)
  ```
- `scale_entries`, `totals_row`, `to_amount`, `format_amount` (`src/adamfit/nutrition.py`): the serving and macro maths.
  ```python
  totals = totals_row(scale_entries(ingredients)).iloc[0]
  ```
- `item_picker`, `entries_editor`, `macro_column_config` (`src/adamfit/ui.py`): the filter and add rows, and the editable table, shared by the log and recipe tabs.
  ```python
  item_picker(
      options,
      key="log_add",
      on_add=lambda option_key, servings: stage_add(changes, option_key, servings),
  )
  ```
- `pending_changes`, `stage_add`, `stage_update`, `stage_delete`, `count_changes`, `apply_changes`, `save_bar` (`src/adamfit/ui.py`): store unsaved changes in session state, show the table as if they were saved, and draw the Save / Revert row.
  ```python
  if save_bar(changes_key):
  ```
- `macro_tiles` (`src/adamfit/ui.py`): draws one boxed `st.metric` tile per macro in a row. Shared with the Home page so both look the same.

## Database tables used
- `food_category`: categories and sub-categories (read).
- `serving_unit`: the units a serving can use, listed in the Foods tab's Unit column (read). To add a unit, insert a row here in a new migration. Nothing else needs changing.
- `standard_food`: the starter list, seeded from `data/food_list.csv` by migration `000010_seed_standard_food`. Never read by the page. A trigger copies it into `food` when a user is created. To change the starter list, edit the CSV and regenerate that migration's INSERT.
- `food`: your foods (read, insert, update, soft delete).
- `recipe`: your recipes (read, insert, update, soft delete).
- `recipe_ingredient`: foods in each recipe (read, insert, update, delete).
- `vw_recipe_nutrition`: view with each recipe's per-serving macros (read).
- `food_log`: what you ate each day (read, insert, update, delete).
