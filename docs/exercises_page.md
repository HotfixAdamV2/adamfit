# Exercises Page

**File:** `src/adamfit/pages/exercises.py` (queries in `src/adamfit/exercises.py`)

## What you see
A **Library** tab (more tabs, such as workouts, will come later) with your own list of exercises. Every user starts with a copy of the 56 standard exercises and can change them freely.

- **Filters.** **Search** finds exercises whose name contains the text (capitals don't matter). **Type** (Strength / Cardio), **Equipment**, **Primary muscle groups** and **Secondary muscle groups** narrow the list further. A filter left empty lets everything through. Filters combine: an exercise must pass all of them. Inside one muscle filter, any of the picked groups is enough, so "Primary: Chest, Triceps" shows exercises whose primary muscles include Chest *or* Triceps. A note says how many exercises are shown, e.g. "Showing 7 of 56 exercises."
- **The table** lists the name, type, equipment, primary and secondary muscle groups, and a **Picture** tick that shows whether the exercise has a picture. Click a row to select it.
- **The details panel** under the table shows the selected exercise: its name, type and equipment (as small badges), its primary and secondary muscle groups, its instructions and its picture (the text on the left, the picture on the right; on a narrow screen they stack). Its **Edit** button opens the **Edit exercise** pop-up. With nothing selected, a note says "Select an exercise to see its instructions and picture." The panel follows the exercise, not the row: if a filter moves it to another row the highlight moves with it, and if a filter hides it (or you remove it) the panel clears. After you save an edit the panel shows the new values.
- **Add exercise** opens the same pop-up, empty, as **Add exercise** (Strength, Bodyweight, no muscle groups).
- **The exercise pop-up** has the name, the type, the equipment, the **Primary** and **Secondary muscle groups** (only for strength exercises), the **Instructions** and a **Picture**. A group picked as primary disappears from the secondary choices, because a muscle is one or the other. The current picture is shown with a **Remove picture** tick box. Choosing a new file (JPEG, PNG, WebP or GIF, up to 5 MB) shows a preview, and it replaces the old picture when you press **Save**. **Save** writes everything at once, **Cancel** (or the X) closes without saving. In Edit, tick **Yes, remove this exercise** and press **Remove exercise** to remove it. If something is wrong (no name, a name you already use, a picture that is too big...), the error shows in the pop-up and it stays open.
- **Manage muscle groups** opens a pop-up listing your own muscle groups and, in a closed **Built-in muscle groups** section, the shared ones, which can't be changed. You can **add** a group, or pick one of yours to **rename** it or (after ticking **Yes, remove this muscle group**) **remove** it. A group still used by active exercises can't be removed; the pop-up says how many and which. A removed group isn't gone for good: adding the same name again brings it back ("Brought back ..."). Names are up to 50 characters and must be unique ignoring capitals, including the built-in names ("chest" clashes with Chest). **Done** (or the X) closes it.

Removed muscle groups are no longer offered in the pickers, but an exercise already tagged with one still shows it, marked "(removed)", when you edit it.

## How it works
1. **One cached table per user.** `get_exercises` reads every active exercise with its tags in one query and keeps the result for an hour. Each exercise's primary and secondary groups come back as lists of ids and names. Every save or remove clears the cache, so the next run reads fresh data.
   ```python
   @st.cache_data(ttl=3600, max_entries=100)
   def get_exercises(user_id: int) -> pd.DataFrame:
   ```
2. **Tabs ready for more.** The page has one tab today. `on_change="rerun"` lets only the open tab's code run.
   ```python
   (library_tab,) = st.tabs(["Library"], key="exercises_tab", on_change="rerun")
   ```
3. **Filtering in pandas.** The filters work on the cached table, so no database query runs while you type. The muscle filters keep a row when it shares at least one group with the picked ones.
   ```python
   if chosen_types:
       view = view[view["exercise_type"].isin(chosen_types)]
   ...
   if chosen_primary:
       view = view[view["primary_ids"].map(lambda ids: has_any(ids, chosen_primary))]
   ```
4. **Selecting a row.** The table uses `on_select` with `selection_mode="single-row"`. A selection only holds a row *position* (0, 1, 2...), which changes when the filters or sort order change. So the `on_select` callback, `remember_selection`, turns it into an exercise id straight away, using the table that was clicked.
   ```python
   rows = st.session_state[TABLE_KEY].selection.rows
   st.session_state[SELECTED_EXERCISE] = int(table.index[rows[0]]) if rows else None
   ```
   On every run, before the table is drawn, the page checks that the remembered exercise is still shown. If not, it forgets it. If it is, it points the table's selection at the row where the exercise is now, so the highlight never lands on a different exercise.
   ```python
   selected_id = st.session_state.get(SELECTED_EXERCISE)
   if selected_id not in table.index:
       selected_id = None
       st.session_state[SELECTED_EXERCISE] = None
   selected_rows = [] if selected_id is None else [table.index.get_loc(selected_id)]
   st.session_state[TABLE_KEY] = {"selection": {"rows": selected_rows}}
   ```
   The panel (`exercise_details`) is drawn from the freshly read table, so a saved edit shows straight away and a removed exercise is simply not found. It only asks the database for the picture when the exercise has one.
   ```python
   image = exercises.get_exercise_image(user_id, exercise_id) if row["has_image"] else None
   ```
   (Earlier versions had an Edit button on every row. It was removed because a button cell inside a selectable table would also select the row; the panel's Edit button does the same job.)
5. **Pop-ups that stay open.** The page draws the open pop-up on every run until one of its buttons, or its X, closes it. One form function makes two pop-ups with different titles.
   ```python
   add_exercise_dialog = st.dialog("Add exercise", width="medium", on_dismiss=close_exercise_dialog)(exercise_form)
   edit_exercise_dialog = st.dialog("Edit exercise", width="medium", on_dismiss=close_exercise_dialog)(exercise_form)
   ```
6. **Primary or secondary, never both.** The form's boxes are filled in from session state when the pop-up opens. Before the Secondary box is drawn, any group already picked as primary is taken out of its choices and its value.
   ```python
   secondary_options = [group_id for group_id in group_names if group_id not in primary_ids]
   st.session_state[f"{key}secondary"] = [
       group_id for group_id in st.session_state[f"{key}secondary"] if group_id in secondary_options
   ]
   ```
7. **Checking a picture.** `check_image` rejects files over 5 MB and reads the file's first bytes to tell its real type, so a renamed text file is refused. The page calls it straight after upload to show a friendly message; `save_exercise` calls it again.
   ```python
   if data.startswith(b"\x89PNG\r\n\x1a\n"):
       return "image/png"
   ```
8. **One transaction per save.** `save_exercise` inserts or updates the exercise, replaces its tags (delete the old ones, insert the new set) and stores or deletes the picture, all inside one `with get_connection() as conn:` block. If anything fails, nothing is saved. Cardio exercises are always saved with no tags.
   ```python
   _write_tags(conn, saved_id, exercise["primary_ids"], exercise["secondary_ids"])
   if image_data is not None:
       _write_image(conn, saved_id, image_data, mime_type, image_file_name)
   ```
9. **Friendly errors.** The database's rules report a SQLSTATE code and a constraint name. `_exercise_error` and `_muscle_group_error` turn them into a `ValueError` with a message, which the pop-up shows.
   ```python
   if e.sqlstate == "23505" and constraint == "unq_exercise_user_id_exercise_name":
       return ValueError("You already have an exercise with that name. Exercise names must be unique.")
   ```
10. **Bringing back a removed group.** Adding a muscle group uses `ON CONFLICT ... DO UPDATE`: if you removed a group with that name earlier, it is made active again. If nothing comes back, the clash was with an active group.
    ```python
    ON CONFLICT (user_id, LOWER(muscle_group_name))
    DO UPDATE SET is_active = TRUE
        WHERE NOT muscle_group.is_active
    ```
11. **Messages inside the Manage muscle groups pop-up.** Add, Rename and Remove do their work in `on_click` callbacks, which run before the pop-up is drawn again. They store a message with `set_dialog_message`, and the right section shows it with `show_dialog_message`. Messages for the whole page (e.g. "Saved Bench press.") use `flash`, so they survive `st.rerun()`.
    ```python
    set_dialog_message(GROUP_MESSAGE, "add", "success", f'{verb} "{name.strip()}".')
    ```

## Widgets used
- [st.title](widgets/st_title.md): the page heading, the exercise name in the details panel (a subheader), and captions for the row count and hints
- [st.tabs](widgets/st_tabs.md): the Library tab
- [st.button](widgets/st_button.md): Add exercise, Manage muscle groups, Edit in the details panel, and Save, Cancel, Remove exercise, Add, Rename, Remove muscle group and Done in the pop-ups
- [st.text_input](widgets/st_text_input.md): the Search filter, the exercise name, and the muscle group name boxes
- [st.segmented_control](widgets/st_segmented_control.md): the Type filter (pick several) and the Type in the pop-up (pick one)
- [st.multiselect](widgets/st_multiselect.md): the Equipment and muscle group filters, and the primary and secondary muscle groups in the pop-up
- [st.selectbox](widgets/st_selectbox.md): the Equipment in the pop-up, and choosing one of your muscle groups to rename or remove
- [st.text_area](widgets/st_text_area.md): the exercise instructions
- [st.file_uploader](widgets/st_file_uploader.md): choosing a picture
- [st.image](widgets/st_image.md): the picture in the details panel, and the current picture and the preview of a new one in the pop-up
- [st.checkbox](widgets/st_checkbox.md): Remove picture, and confirming a removal
- [st.dataframe](widgets/st_dataframe.md): the exercise table, with single-row selection and a `CheckboxColumn` for Picture
- [st.dialog](widgets/st_dialog.md): the Add exercise, Edit exercise and Manage muscle groups pop-ups
- [st.markdown](widgets/st_markdown.md): the type and equipment badges, muscle groups and instructions in the details panel, and the list of your muscle groups
- [st.success / st.error / st.info](widgets/st_status_messages.md): saved messages, errors and "No exercises match these filters."
- [st.container / st.columns / st.expander / st.divider](widgets/st_layout.md): rows of filters and buttons, the bordered details panel with its two columns, the Built-in muscle groups section, and the lines between pop-up sections

## Core functions
- `get_exercises` (`src/adamfit/exercises.py`): the user's active exercises with type, equipment, instructions (an empty string when there are none, because pandas would turn a missing value into NaN, which counts as true), tag ids and names, and whether there is a picture. Cached per user.
  ```python
  library = exercises.get_exercises(user_id)
  ```
- `get_exercise_types`, `get_equipment` (`src/adamfit/exercises.py`): the lookup lists as `{code: name}`, cached for an hour.
  ```python
  types = exercises.get_exercise_types()
  ```
- `get_muscle_groups` (`src/adamfit/exercises.py`): active built-in groups plus the user's own, with `is_own`. Cached per user.
  ```python
  groups = exercises.get_muscle_groups(user_id)
  ```
- `save_exercise` (`src/adamfit/exercises.py`): adds (`exercise_id=None`) or edits an exercise, its tags and its picture in one transaction. Raises `ValueError` with a message for the user.
  ```python
  exercises.save_exercise(
      user_id,
      exercise_id,
      values,
      image_data=new_image,
      image_file_name=upload.name if upload is not None else None,
      remove_image=remove_picture,
  )
  ```
- `remove_exercise` (`src/adamfit/exercises.py`): hides an exercise (`is_active = FALSE`).
  ```python
  exercises.remove_exercise(user_id, exercise_id)
  ```
- `get_exercise_image`, `check_image` (`src/adamfit/exercises.py`): load an exercise's picture (the last few are cached), and check an upload's size and type.
  ```python
  current = exercises.get_exercise_image(user_id, exercise_id) if exercise_id is not None else None
  ```
- `add_muscle_group`, `rename_muscle_group`, `remove_muscle_group` (`src/adamfit/exercises.py`): change the user's own groups. Adding returns `(id, brought_back)`. Removing a group still in use raises a `ValueError` naming the exercises.
  ```python
  _, brought_back = exercises.add_muscle_group(user_id, name)
  ```
- `exercise_details`, `remember_selection` (`src/adamfit/pages/exercises.py`): the details panel, and the table's `on_select` callback that turns the selected row into an exercise id.
  ```python
  exercise_details(selected_id, library.loc[selected_id])
  ```
- `exercise_form`, `group_dialog`, `open_exercise_dialog`, `close_exercise_dialog`, `open_group_dialog`, `close_group_dialog`, `has_any` (`src/adamfit/pages/exercises.py`): the pop-ups, the helpers that remember which one is open, and the muscle filter test.
- `flash`, `show_flash`, `set_dialog_message`, `show_dialog_message` (`src/adamfit/ui.py`): messages that survive a rerun, for the page and for one section of a pop-up.

## Database tables used
- `exercise`: read; rows added, edited and hidden (`is_active = FALSE`).
- `exercise_muscle_group`: read; an exercise's rows are deleted and re-inserted on every save.
- `exercise_image`: read; a picture is inserted or replaced (`ON CONFLICT (exercise_id) DO UPDATE`) or deleted.
- `muscle_group`: read; the user's own groups are added, renamed, hidden or brought back.
- `exercise_type`, `equipment`: read only (lookup lists).
