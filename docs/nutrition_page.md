# Nutrition Page

**File:** `src/adamfit/pages/nutrition.py`

## What you see
Three tabs:
1. **Daily log**: pick a day (with ‹ and › buttons for the previous and next day). Narrow the list with the **Category** and **Sub-category** boxes, search for a food or recipe, enter how many servings you ate and press **Add**. Recipes have their own "Recipes" entry in Category. A small note next to the box shows what one serving is (e.g. "1 serving = 30 g"). The table lists everything for that day with its servings, the amount those servings come to (e.g. "45 g"), then fat, carbs, protein, fiber and calories. Change the servings, or select rows and press Delete. The day's totals sit underneath as a row of boxed tiles, the same as on the Home page. Below the log, a **Macros over time** card (with a **Show** switch to fold it away) charts calories (or fat, carbs, protein or fiber) per day with a rolling average. It defaults to the last 3 months and a 7-day average; you can pick another period or your own dates, change the window, and turn either line off. Days you logged nothing are left out rather than counted as zero. Hovering shows that day's total and average together. It is the same chart as on the Home page (see [Charts over time](charts.md)), and only shows saved entries.
2. **Recipes**: choose a recipe or create one with **New recipe** (name, how many servings it makes, and what one serving is called, e.g. "bowl"). You see its macros per serving, an ingredients table that works like the daily log (with the same filters, foods only, and the whole-recipe **Total** row under the table), and the instructions. **Edit recipe details** changes the name, yield and instructions, or deletes the recipe. These save straight away.
3. **Foods**: your own food list, filterable by category and searchable by name. The table is read-only. Press **Edit** on a row to open the **Edit food** pop-up, filled in with that food: name, category, serving size and unit, and the macros for one serving. **Save** writes the change straight away, **Cancel** (or the X) closes without saving. To remove the food, tick **Yes, remove this food** and press **Delete food**. **Add food** (next to the filters) opens the same pop-up, empty, as **Add food**, with the unit set to g and the macros to 0. If something is wrong (no name, no category, a name you already use...), the error shows in the pop-up and it stays open.
   - **Your own categories.** The Category box lists sub-categories (e.g. "Protein › Poultry"), because every food sits in one. The last choice, **+ New category**, shows two more boxes: **Put it under** (any top-level category, or **+ New top-level category** with a box for its name) and **Sub-category name**. Save creates the category (and the new top-level one) together with the food. If the food can't be saved, the new category isn't kept either.
   - **Manage categories** (next to Add food) opens a pop-up that lists your own categories under their top-level category. Built-in top-level categories are marked :material/lock: *Built-in*, and the full built-in list is in a closed **Built-in categories** section. Built-in categories are shared by everyone and can't be changed. You can **add** a sub-category under any top-level category, or a new top-level category together with its first sub-category. Pick one of yours to **rename** it, or tick **Yes, remove this category** and press **Remove category**. A category that still holds active foods or sub-categories can't be removed, and the pop-up says so. A removed category isn't gone for good: adding the same name under the same parent again brings it back ("Brought back ..." instead of "Added ..."), with its old spelling. For the same reason you can't rename another category to a name you removed there; the pop-up tells you to add it again instead. **Done** (or the X) closes it. Names are up to 50 characters and must be unique under the same parent, ignoring capitals ("rice" and "Rice" clash), including built-in names.

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
13. **An Edit button on every row.** The Foods table is a read-only `st.dataframe`. Its first column is a `ButtonColumn`: every cell holds the label ":material/edit: Edit", so every row gets a button. Pressing one calls `open_clicked_food` before the next run. The click's `row` is the row's position in the table, which the page turns into a food id.
    ```python
    "edit": st.column_config.ButtonColumn(
        "Edit", type="tertiary", on_click=open_clicked_food, key="food_edit_click"
    ),
    ...
    click = st.session_state["food_edit_click"]
    open_food_dialog(int(view.index[click.row]))
    ```
14. **Remembering that a pop-up is open.** A button click only counts on the run right after it, and the click resets by itself. So `open_food_dialog` stores the food id (None for **Add food**) in `st.session_state["editing_food"]`, and `open_category_dialog` sets `st.session_state["managing_categories"]`. At the end of the tab the matching pop-up is drawn on every run while its key is set, which keeps it open even if the whole page reruns. Only one pop-up can be open at a time, so each open function removes the other key.
    ```python
    if EDITING_FOOD in st.session_state:
        food_id = st.session_state[EDITING_FOOD]
        if food_id is None:
            add_food_dialog(None)
        elif food_id in food_list.index:
            edit_food_dialog(food_id)
        else:
            close_food_dialog()
    elif MANAGING_CATEGORIES in st.session_state:
        category_dialog()
    ```
15. **One form, two pop-ups.** `food_form` draws the food's boxes. `st.dialog` is applied to it twice to get the two titles. Save, Cancel, Delete food and the X all call `close_food_dialog`, which removes `editing_food`. The X does this through `on_dismiss`. The boxes are not inside a `st.form`: in a form, choosing "+ New category" could not show the extra boxes until Save was pressed. A pop-up reruns on its own, so without a form it reacts straight away.
    ```python
    add_food_dialog = st.dialog("Add food", width="medium", on_dismiss=close_food_dialog)(food_form)
    edit_food_dialog = st.dialog("Edit food", width="medium", on_dismiss=close_food_dialog)(food_form)
    ```
16. **Saving one food.** Save passes a single add, or a single update keyed by the food id, to `save_food_changes`. Its checks raise `ValueError` with a message for the user. The page shows that inside the pop-up and leaves it open. On success it closes the pop-up, stores a message with `flash` and calls `st.rerun()`. The whole page then runs again and reloads the food list, so the Daily log and Recipes pickers see the change too. A staged log or recipe add of a food that was just removed is dropped by `apply_changes`.
    ```python
    try:
        if category_id == NEW_CATEGORY:
            ...  # see step 19
        elif food_id is None:
            foods.save_food_changes(user_id, [new_values], {}, [])
        else:
            foods.save_food_changes(user_id, [], {food_id: new_values}, [])
    except ValueError as e:
        st.error(str(e))
    else:
        close_food_dialog()
        flash(message)
        st.rerun()
    ```
17. **Categories: built-in and your own.** In `food_category`, a row with no `user_id` is a built-in category everyone sees, and a row with your `user_id` is yours. `get_categories` reads the active built-in sub-categories plus your own, with an `is_own` flag, and `get_parent_categories` reads the top-level ones. Both are cached for an hour per user (`st.cache_data` keys the cache by `user_id`), and every add, rename or remove clears that user's entry so the change shows straight away.
    ```python
    WHERE fc.is_active
        AND (fc.user_id IS NULL OR fc.user_id = %s)
    ...
    get_categories.clear(user_id)
    get_parent_categories.clear(user_id)
    ```
    The Foods filter, the food pop-up and the Daily log / Recipes pickers all build their lists from `get_categories` or from your food list, so your own categories show up in all of them.
18. **The database guards the rules.** Duplicate names, a parent that belongs to someone else, and removing a category that is still in use are all refused by the database (migrations 000018 to 000021). Each refusal comes with a code (`e.sqlstate`) and a rule name (`e.diag.constraint_name`). `_category_error` in `foods.py` turns those into messages for you, and for "still in use" it passes on the database's own message. The database does *not* stop a built-in row being renamed, so every rename and remove only matches your own rows:
    ```python
    WHERE category_id = %s
        AND user_id = %s
        AND is_active
    ```
19. **A new category and its food in one transaction.** When "+ New category" is chosen, Save calls `save_food_in_new_category`. It creates the new top-level category (if any), then the sub-category, then saves the food, all on one connection. If any step fails, the database rolls all of them back, so a failed food save never leaves an empty category behind.
    ```python
    if category_id == NEW_CATEGORY:
        category_name, parent_id, new_parent_name = new_category_values("food_new_category")
        _, brought_back = foods.save_food_in_new_category(
            user_id, food_id, new_values, category_name, parent_id, new_parent_name
        )
    ```
20. **The Manage categories pop-up uses callbacks.** Add category, Rename and Remove category each have an `on_click` function. It runs before the pop-up is drawn again, so it can save, clear the name boxes, and store a message (`set_category_message`) that the right section then shows (`show_category_message`). The pop-up reads the categories itself, so the lists in it are always up to date. When it closes, the whole page reruns and the filters pick up the changes.
    ```python
    def add_clicked() -> None:
        try:
            name, parent_id, new_parent_name = new_category_values("manage_new")
            _, brought_back = foods.add_category(user_id, name, parent_id, new_parent_name)
        except ValueError as e:
            set_category_message("add", "error", str(e))
            return
    ```
    Removing a category keeps its row (soft delete), and the database allows only one row per owner, parent and name, active or not (migration 000021). So `_insert_category` uses `ON CONFLICT`: if the name clashes with one of your removed categories, that row is made active again instead of a second one being added. `xmax <> 0` is true when the row was updated rather than inserted, which is how the page knows to say "Brought back". No row back means the clash was with an active category, so the name is taken.
    ```python
    INSERT INTO food_category (user_id, category_name, parent_category_id)
    VALUES (%s, %s, %s)
    ON CONFLICT (user_id, parent_category_id, LOWER(category_name))
    DO UPDATE SET is_active = TRUE
        WHERE NOT food_category.is_active
    RETURNING category_id, xmax <> 0 AS brought_back
    ```
    The chosen parent is checked to be active first, so nothing is added (or brought back) under a removed parent, e.g. one removed in another browser tab.

    A new top-level category must come with its first sub-category. Foods can only go in sub-categories, so an empty top-level one would be no use. If you later remove all its sub-categories, it stays listed (as "No sub-categories yet") so you can add one or remove it.
21. **Deleting is a soft delete.** Removing a food, recipe or category sets `is_active = FALSE` (a removed category can be brought back by adding it again, see step 20). It disappears from your lists, but recipes and past days that used it keep their numbers. Log entries and ingredients are really deleted.
22. **Macros over time** (Daily log tab). Below the save row, the shared chart from `charts.py` is drawn in a card with its own key prefix. When the card's Show switch is off, the chart and its query don't run. It reads saved entries only, so unsaved changes appear in it after Save changes. One macro is shown at a time, because calories and grams are on very different scales. Days with nothing logged have no row, so the rolling average covers logged days only. See [Charts over time](charts.md).
    ```python
    # Shared with the Home page (see charts.py). It shows saved entries
    # only, so unsaved changes above appear here after Save changes.
    charts.chart_card(
        "Macros over time",
        "nutrition_macros",
        lambda key: charts.show_macros_over_time(user_id, key),
    )
    ```

## Widgets used
- [st.tabs](widgets/st_tabs.md): the Daily log, Recipes and Foods tabs
- [st.data_editor](widgets/st_data_editor.md): the editable log and ingredient tables
- [st.dataframe](widgets/st_dataframe.md): the Total row under a recipe's ingredients table, and the read-only food list, with an Edit button on every row (`st.column_config.ButtonColumn`) that opens the Edit food pop-up
- [st.dialog](widgets/st_dialog.md): the Add food and Edit food pop-ups, and the Manage categories pop-up
- [st.checkbox](widgets/st_checkbox.md): confirming a food delete or a category removal
- [st.selectbox](widgets/st_selectbox.md): the Category and Sub-category filters, picking a food, recipe or category, "Put it under" for a new category, and the category to rename or remove
- [st.number_input](widgets/st_number_input.md): servings to add, a recipe's number of servings, a food's serving size and macros, and the chart's rolling-average days
- [st.date_input](widgets/st_date_input.md): the day being logged, and the custom date range of the Macros over time chart
- [st.segmented_control](widgets/st_segmented_control.md): the macro to chart and its time period
- [st.pills](widgets/st_pills.md): turns the daily total and average lines on or off
- [st.altair_chart](widgets/st_altair_chart.md): the Macros over time chart
- [st.fragment](widgets/st_fragment.md): reruns only the Macros over time chart when its controls change
- [st.toggle](widgets/st_toggle.md): the Show switch on the Macros over time card
- [st.button](widgets/st_button.md): Add, previous/next day, Save changes, Revert changes, confirming a recipe delete, Add food, Manage categories, Save, Cancel and Delete food in the food pop-up, and Add category, Rename, Remove category and Done in the Manage categories pop-up
- [st.text_input](widgets/st_text_input.md): recipe name, serving label, food search, food name, and category names
- [st.text_area](widgets/st_text_area.md): recipe instructions
- [st.markdown](widgets/st_markdown.md): shows the instructions, small bold headings, and the grouped list of your categories
- [st.metric](widgets/st_metric.md): the day's totals in the Daily log, and a recipe's macros per serving
- [st.form / st.form_submit_button](widgets/st_form.md): the New recipe and recipe details forms (the food pop-up is not a form, see step 15)
- [st.popover](widgets/st_popover.md): the New recipe form and the delete confirmation
- [st.container / st.columns / st.expander / st.divider](widgets/st_layout.md): the bordered Macros over time card, the filter, add and save rows, the Edit recipe details section, the line above Delete food, the box around the new-category fields, and the Built-in categories expander
- [st.title / st.subheader / st.caption](widgets/st_title.md): headings, hints, the "1 serving = ..." note and the unsaved-changes count
- [st.info / st.warning / st.error / st.success](widgets/st_status_messages.md): empty states, unsaved changes on other days, errors and save messages

## Core functions
- `get_log`, `save_log_changes` (`src/adamfit/food_logs.py`): read one day's log, and save a batch of adds, servings changes and deletes in one transaction. Raises `ValueError` if a number is too large.
  ```python
  food_logs.save_log_changes(user_id, log_date, adds, changes["updates"], changes["deletes"])
  ```
- `get_daily_totals` (`src/adamfit/food_logs.py`): one row per logged day with the summed macros (each entry's per-serving macros × servings, foods and recipes both included), for the Macros over time chart.
- `chart_card` and `show_macros_over_time` (`src/adamfit/charts.py`): the card with a Show switch, and the Macros over time chart with its controls, shared with the Home page.
  ```python
  charts.chart_card(
      "Macros over time",
      "nutrition_macros",
      lambda key: charts.show_macros_over_time(user_id, key),
  )
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
- `get_foods`, `get_categories`, `get_serving_units`, `save_food_changes` (`src/adamfit/foods.py`): read and save the food list. `get_foods` also returns each food's parent and sub-category names for the filters, and is read fresh on every run (not cached). Categories (per user) and units are cached for an hour. `save_food_changes` takes lists of adds, updates and deletes. The Foods tab passes one change at a time. It raises `ValueError` if a food is invalid or its name is already used.
  ```python
  food_list = foods.get_foods(user_id)
  ...
  foods.save_food_changes(user_id, [], {}, [food_id])
  ```
- `get_categories`, `get_parent_categories` (`src/adamfit/foods.py`): the active sub-categories and top-level categories you can use (built-in plus your own, with `is_own`). Cached per user.
  ```python
  categories = foods.get_categories(user_id)
  ```
- `add_category`, `rename_category`, `remove_category` (`src/adamfit/foods.py`): manage your own categories. Names are trimmed and must be 1 to 50 characters. `add_category` can also create a new top-level parent in the same transaction, and returns `(category_id, brought_back)`: adding a name you removed earlier brings that category back. `rename_category` refuses a name you removed under the same parent, with a message saying to add it again. All three raise `ValueError` with a message for the user (e.g. `'"Fruit" already exists here.'`) and clear the category cache on success.
  ```python
  _, brought_back = foods.add_category(user_id, name, parent_id, new_parent_name)
  foods.rename_category(user_id, category_id, new_name)
  foods.remove_category(user_id, category_id)
  ```
- `save_food_in_new_category` (`src/adamfit/foods.py`): creates a category (and its new parent) and saves one food in it, in one transaction. Used by "+ New category" in the food pop-up. Like `add_category`, it brings back a removed category with that name and returns `(category_id, brought_back)`.
- `food_form`, `open_food_dialog`, `close_food_dialog`, `open_clicked_food` (`src/adamfit/pages/nutrition.py`): the food pop-up, and opening and closing it.
  ```python
  st.button(
      "Add food",
      type="primary",
      icon=":material/add:",
      on_click=open_food_dialog,
      args=(None,),
  )
  ```
- `category_dialog`, `open_category_dialog`, `close_category_dialog`, `new_category_fields`, `new_category_values`, `set_category_message`, `show_category_message` (`src/adamfit/pages/nutrition.py`): the Manage categories pop-up, the shared "Put it under" / name boxes used by both pop-ups, and the messages shown inside the pop-up.
  ```python
  new_category_fields("manage_new")
  st.button("Add category", icon=":material/add:", on_click=add_clicked, key="manage_add")
  show_category_message("add")
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
- `food_category`: built-in and your own categories and sub-categories (read; insert, rename and soft delete of your own rows only).
- `serving_unit`: the units a serving can use, offered in the food pop-up's Serving unit box (read). To add a unit, insert a row here in a new migration. Nothing else needs changing.
- `standard_food`: the starter list, seeded from `data/food_list.csv` by migration `000010_seed_standard_food`. Never read by the page. A trigger copies it into `food` when a user is created. To change the starter list, edit the CSV and regenerate that migration's INSERT.
- `food`: your foods (read, insert, update, soft delete).
- `recipe`: your recipes (read, insert, update, soft delete).
- `recipe_ingredient`: foods in each recipe (read, insert, update, delete).
- `vw_recipe_nutrition`: view with each recipe's per-serving macros (read).
- `food_log`: what you ate each day (read, insert, update, delete).
