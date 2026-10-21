# Exercises Page

**File:** `src/adamfit/pages/exercises.py`

## What you see
A table listing every exercise in the database: its id, name and the muscle group it works.

## How it works
1. The page shows a heading.
   ```python
   st.title("Exercises")
   ```
2. It asks the database for all rows in the `exercise` table, sorted by name.
   ```python
   rows = fetch_all(
       """
       SELECT
           exercise_id,
           exercise_name,
           muscle_group
       FROM exercise
       ORDER BY exercise_name
       """
   )
   ```
3. The rows are shown in a table, with the row-number column hidden.
   ```python
   st.dataframe(rows, hide_index=True)
   ```

## Widgets used
- [st.title](widgets/st_title.md): the page heading
- [st.dataframe](widgets/st_dataframe.md): shows the exercise table. We pass `hide_index=True` to hide the row numbers.

## Core functions
- `fetch_all` (`src/adamfit/db.py`): borrows a connection from the shared pool (see [Streamlit basics](streamlit_basics.md#4-the-connection-pool)), runs a SELECT query, returns the connection to the pool, and returns the rows as a list of dictionaries.
  ```python
  rows = fetch_all("SELECT exercise_name FROM exercise WHERE muscle_group = %s", ("Back",))
  ```

## Database tables used
- `exercise`: read only.
