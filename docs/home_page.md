# Home Page

**File:** `src/adamfit/app.py`

## What you see
A welcome message and a green or red box telling you whether the app can reach the database.

## How it works
1. The browser tab title and icon are set.
   ```python
   st.set_page_config(page_title="AdamFit", page_icon=":muscle:")
   ```
2. The heading and welcome text are shown.
   ```python
   st.title("AdamFit")
   st.write("Welcome to my personal fitness app.")
   ```
3. The shared connection pool is created (first run only), then a trivial query (`SELECT 1`) tests the database. A success box is shown if it works, otherwise the error is shown.
   ```python
   try:
       get_pool()  # create the shared connection pool on first run
       fetch_all("SELECT 1 AS ok")
       st.success("Connected to the database.")
   except Exception as exc:
       st.error(f"Could not connect to the database: {exc}")
   ```

## Widgets used
- [st.set_page_config](widgets/st_set_page_config.md): sets the tab title and icon
- [st.title](widgets/st_title.md): the page heading
- [st.write](widgets/st_write.md): the welcome text
- [st.success / st.error](widgets/st_status_messages.md): shows whether the connection worked

## Core functions
- `fetch_all` (`src/adamfit/db.py`): borrows a pooled connection, runs a query and returns the rows.
  ```python
  fetch_all("SELECT 1 AS ok")
  ```
- `get_pool` (`src/adamfit/db.py`): creates the shared connection pool the first time it is called, using the settings in the `.env` file. The page calls it once so the pool is ready. See [Streamlit basics](streamlit_basics.md#4-the-connection-pool).
  ```python
  get_pool()
  ```
- `get_connection` (`src/adamfit/db.py`): borrows a connection from the pool for a `with` block. `fetch_all` uses it for you.
