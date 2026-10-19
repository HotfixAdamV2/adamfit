# Nutrition Page

**File:** `src/adamfit/pages/nutrition.py`

## What you see
Three tabs:
1. **Daily log**: pick a day (with ‹ and › buttons for the previous and next day), search for a food or recipe, enter how much you ate and press **Add**. The table lists everything for that day with its calories, protein, carbs, fat and fiber. Change an amount and the macros update straight away. Select rows and press Delete to remove them. A **Total** row sits underneath.
2. **Recipes**: choose a recipe or create one with **New recipe** (name, how many servings it makes, and what one serving is called, e.g. "bowl"). You see its macros per serving, an ingredients table that works like the daily log, and the instructions. **Edit recipe details** changes the name, yield and instructions, or deletes the recipe.
3. **Foods**: your own food list, filterable by category and searchable by name. Edit any cell, add a food in the empty bottom row, or select rows and press Delete. Nothing is saved until you press **Save changes**.

Amounts are shown in the food's own serving unit (tbsp, piece, bar...). Foods measured by **weight** (g or oz) are shown in your preferred unit: ounces for imperial, grams for metric. A food with a 4 oz serving shows as 113.4 g to a metric user.

## How it works
1. **One serving per food.** Every food has one serving (e.g. 4 oz, or 1 tbsp) and its macros are for that serving. The log and recipes store a *number of servings*. `nutrition.py` turns servings into the amount you see (e.g. 8 oz) and back. Whether a unit is a weight, and how many grams it holds, comes from the `serving_unit` table (`grams_per_unit`).
   ```python
   def to_servings(
       amount: float,
       serving_size: float,
       grams_per_unit: float | None,
       unit_system: str,
   ) -> float:
       if _is_weight(grams_per_unit):
           amount = amount * _display_weight(unit_system)[1] / grams_per_unit
       return round(amount / serving_size, 3)
   ```
2. **Tabs that remember where you are.** `on_change="rerun"` makes the tabs track which one is open, so it stays open after a save, and only that tab's code runs.
   ```python
   log_tab, recipe_tab, food_tab = st.tabs(
       ["Daily log", "Recipes", "Foods"], key="nutrition_tab", on_change="rerun"
   )
   ...
   if log_tab.open:
       with log_tab:
   ```
3. **Adding a row.** `item_picker` (in `ui.py`) shows a searchable list, an amount box and an Add button. The amount box has a different key per item, so it resets to one serving whenever you pick something else. Clicking Add runs a callback that saves the row and clears the picker.
   ```python
   st.number_input(
       f"Amount ({unit})",
       min_value=0.01,
       value=round(one_serving, 1),
       step=1.0,
       format="%.1f",
       width=150,
       key=f"{key}_amount_{choice}",
   )
   st.button("Add", icon=":material/add:", type="primary", disabled=choice is None, on_click=_add)
   ```
4. **Editing amounts live.** `entries_editor` (in `ui.py`) shows a `st.data_editor` where only Amount can be changed. Its `on_change` callback saves every edit or delete to the database before the rerun, then bumps a version number in the key. The new key gives a fresh editor, so the redrawn table shows the new macros from the database.
   ```python
   def _save() -> None:
       changes = st.session_state[editor_key]
       deleted = set(changes["deleted_rows"])
       for position in deleted:
           on_delete(ids[position])
       for position, edits in changes["edited_rows"].items():
           ...
               on_update(ids[position], servings)
       st.session_state[version_key] += 1
   ```
5. **The totals row.** A data editor cannot have a fixed bottom row, so the totals are a one-row `st.dataframe` drawn directly under it, using the same column settings so the columns line up.
   ```python
   st.dataframe(
       totals_row(scaled),
       hide_index=True,
       column_config=column_config,
       alt=f"Totals for: {alt}",
   )
   ```
6. **Recipe macros are calculated, not typed.** The `vw_recipe_nutrition` view adds up `servings × macro` for each ingredient and divides by the recipe's yield. The page shows those per-serving values as metrics, with the whole-recipe totals in each tooltip.
   ```python
   st.metric(
       macro_label,
       f"{float(recipe[column]):,.0f}" if column == "calories" else f"{float(recipe[column]):.1f}",
       help=f"Whole recipe: {total:,.1f}",
       border=True,
   )
   ```
7. **Selecting a new recipe.** A widget's value can only be set *before* the widget is drawn. After creating (or deleting) a recipe, the page stores the choice in `pending_recipe_choice` and applies it on the next run, just before the selectbox.
   ```python
   if "pending_recipe_choice" in st.session_state:
       st.session_state["recipe_choice"] = st.session_state.pop("pending_recipe_choice")
   ```
8. **Saving the food list.** The Foods editor sits inside a form, so edits are batched. On **Save changes**, the added, edited and deleted rows are collected and saved in one transaction, so either everything is saved or nothing is. The editor's key includes the filters, because edits are matched to rows by position.
   ```python
   foods.save_food_changes(user_id, changes["added_rows"], updates, deletes)
   ```
9. **Deleting is a soft delete.** Removing a food or recipe sets `is_active = FALSE`. It disappears from your lists, but recipes and past days that used it keep their numbers.

## Widgets used
- [st.tabs](widgets/st_tabs.md): the Daily log, Recipes and Foods tabs
- [st.data_editor](widgets/st_data_editor.md): the editable log, ingredient and food tables
- [st.dataframe](widgets/st_dataframe.md): the Total row under each editable table
- [st.selectbox](widgets/st_selectbox.md): picking a food, recipe or category
- [st.number_input](widgets/st_number_input.md): amount to add, and a recipe's number of servings
- [st.date_input](widgets/st_date_input.md): the day being logged
- [st.button](widgets/st_button.md): Add, previous/next day, and confirming a delete
- [st.text_input](widgets/st_text_input.md): recipe name, serving label and food search
- [st.text_area](widgets/st_text_area.md): recipe instructions
- [st.markdown](widgets/st_markdown.md): shows the instructions and small bold headings
- [st.metric](widgets/st_metric.md): a recipe's macros per serving
- [st.form / st.form_submit_button](widgets/st_form.md): new recipe, recipe details and the food list
- [st.popover](widgets/st_popover.md): the New recipe form and the delete confirmation
- [st.container / st.columns / st.expander](widgets/st_layout.md): rows of widgets and the Edit recipe details section
- [st.title / st.subheader / st.caption](widgets/st_title.md): headings and hints
- [st.info / st.error / st.success](widgets/st_status_messages.md): empty states, validation errors and save messages

## Core functions
- `get_log`, `add_entry`, `update_entry`, `delete_entry` (`src/adamfit/food_logs.py`): read and change one day's log.
  ```python
  log = food_logs.get_log(user_id, log_date)
  ```
- `get_recipes`, `get_recipe`, `create_recipe`, `update_recipe`, `delete_recipe` (`src/adamfit/recipes.py`): manage recipes. Create and update raise `ValueError` if the name is taken.
  ```python
  recipe = recipes.get_recipe(user_id, recipe_id)
  ```
- `get_ingredients`, `add_ingredient`, `update_ingredient`, `delete_ingredient` (`src/adamfit/recipes.py`): manage a recipe's ingredients.
  ```python
  ingredients = recipes.get_ingredients(user_id, recipe_id)
  ```
- `get_foods`, `get_categories`, `get_serving_units`, `save_food_changes` (`src/adamfit/foods.py`): read and save the food list. Categories and units are cached for an hour.
  ```python
  food_list = foods.get_foods(user_id)
  ```
- `scale_entries`, `totals_row`, `to_amount`, `to_servings`, `amount_unit` (`src/adamfit/nutrition.py`): the serving and macro maths.
- `item_picker`, `entries_editor`, `macro_column_config` (`src/adamfit/ui.py`): the add row and the live-editing table, shared by the log and recipe tabs.
  ```python
  entries_editor(
      log,
      key="log_table",
      unit_system=unit_system,
      on_update=lambda entry_id, servings: food_logs.update_entry(user_id, entry_id, servings),
      on_delete=lambda entry_id: food_logs.delete_entry(user_id, entry_id),
      alt=f"Food log for {log_date:%b %d, %Y}",
  )
  ```

## Database tables used
- `food_category`: categories and sub-categories (read).
- `serving_unit`: the units a serving can use, and grams per unit for weights (read). To add a unit, insert a row here in a new migration. Nothing else needs changing.
- `standard_food`: the starter list. Never read by the page. A trigger copies it into `food` when a user is created.
- `food`: your foods (read, insert, update, soft delete).
- `recipe`: your recipes (read, insert, update, soft delete).
- `recipe_ingredient`: foods in each recipe (read, insert, update, delete).
- `vw_recipe_nutrition`: view with each recipe's total and per-serving macros (read).
- `food_log`: what you ate each day (read, insert, update, delete).
