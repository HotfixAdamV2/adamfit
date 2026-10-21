# Streamlit Basics and How AdamFit Is Organized

A beginner's guide to how Streamlit works, how this project is laid out, and how to start reading the code.

## 1. How Streamlit works

### The script reruns from top to bottom
A Streamlit app is just a Python script. Each time something happens (the page loads, someone clicks a button, types in a box), Streamlit **runs the whole script again from the first line to the last**. Whatever the script displays on that run is what the user sees.

```python
st.title("Exercises")                 # runs every time
rows = fetch_all("SELECT ...")        # runs every time
st.dataframe(rows)                    # runs every time
```

This is simple, but it means anything slow or expensive (like opening a database connection) would repeat on every click unless we do something about it.

### Server and browser
The Python code runs on the **server** (your machine, for now). The **browser** only displays what the server sends and reports clicks back. Each browser tab is its own **session**, but all sessions are served by the same Python process.

### Remembering things: `st.session_state`
Variables are reset on every rerun. `st.session_state` is a dictionary that survives reruns, and is private to one browser session (one user). Use it for things like "which workout is currently selected".

```python
if "count" not in st.session_state:
    st.session_state.count = 0
```

### Caching: `cache_data` vs `cache_resource`
| Decorator | Use for | Behaviour |
|-----------|---------|-----------|
| `@st.cache_data` | Results such as query results or computed tables | Stores a *copy* of the return value per input |
| `@st.cache_resource` | Shared objects such as connection pools or ML models | Stores the *one object itself*, shared by every user and rerun |

We use `@st.cache_resource` for the database connection pool (see section 4).

### Multipage apps and the router
The file you pass to `streamlit run` is `app.py`. In AdamFit it isn't a page itself. It is a **router**: it runs on every interaction, decides which pages exist using [`st.navigation`](widgets/st_navigation.md), and then runs the one the user picked.

```python
if user is None:
    page = st.navigation([st.Page("pages/login.py", title="Log in")])
else:
    page = st.navigation({"Home": [...], "Me": [...], "Nutrition": [...], "Library": [...]})
    with st.sidebar:
        ...  # "Logged in as ..." and the Log out button
page.run()
```

Logged-out visitors only have the login page, so other pages can't be reached even by typing their URL. **To add a page**, create the file in `pages/` and register it with an `st.Page` in `app.py`. See [authentication](authentication.md) for how login works.

### Controlling the run: `st.rerun` and `st.stop`
- `st.rerun()` starts the script again immediately. We use it after saving something, so the page redraws with fresh data.
- `st.stop()` ends the current run early. Nothing below it is drawn. We use it when there's nothing more to show (e.g. no weigh-ins yet).

## 2. How AdamFit is organized

| Path | What lives there |
|------|------------------|
| `src/adamfit/app.py` | The entry point and router: picks which pages exist, and the sidebar. Also finishes a Google Health connection when Google redirects back |
| `src/adamfit/pages/` | One file per page (`login.py`, `home.py`, `profile.py`, `exercises.py`) |
| `src/adamfit/db.py` | The connection pool and generic query helpers (`fetch_all`, `fetch_one`, `execute`) |
| `src/adamfit/auth.py` | Password hashing and who is logged in |
| `src/adamfit/users.py`, `weights.py` | Queries for one table each (`app_user`, `user_weight`) |
| `src/adamfit/google_health.py`, `google_health_connection.py` | Google Health (Fitbit) login and weight sync, and the queries for its `google_health_connection` table |
| `src/adamfit/units.py` | lb/kg and ft-in/cm conversions |
| `src/adamfit/ui.py` | Small helpers shared by pages (flash messages) |
| `src/adamfit/cli/` | Terminal commands, such as `adamfit-create-user` |
| `docs/` | One markdown file per page (`*_page.md`) and this guide |
| `docs/widgets/` | One short explanation per Streamlit widget, shared by all pages |
| `database/` | Docker setup for Postgres, setup SQL, and `migrations/` that build the tables |
| `.env` | Settings for the app (database login, pool sizes). Never committed |
| `instructions.md`, `.claude/` | Guidance, skills and agents for AI assistants |

The path of one request:

```
Browser -> app.py (router) -> page script (pages/profile.py) -> weights.py / users.py -> db.py -> connection pool -> Postgres
```

## 3. How to start reading the code
Read in this order:

1. [README.md](../README.md): how to run everything.
2. `src/adamfit/app.py`: the router. Shows how pages and login fit together.
3. `src/adamfit/pages/login.py` and `src/adamfit/auth.py`: how logging in works ([authentication](authentication.md)).
4. `src/adamfit/db.py`: how the database is reached.
5. `src/adamfit/pages/exercises.py`: the simplest page that reads from the database.
6. `src/adamfit/pages/profile.py` with `users.py`, `weights.py` and `units.py`: a full page that reads, writes and charts.
7. The matching page docs ([login](login_page.md), [home](home_page.md), [profile](profile_page.md), [exercises](exercises_page.md)): explain each step with snippets.
8. Widget docs in [widgets/](widgets/README.md): look up anything like `st.dataframe` you don't recognize.
9. `database/migrations/`: how the tables are created.

**Follow one example:** open the Exercises page.
1. Streamlit runs `app.py`, which sees you're logged in, registers the pages, and runs `pages/exercises.py` from the top.
2. `st.title` draws the heading.
3. `fetch_all(...)` is called. It borrows a connection from the pool, runs the SELECT, and returns the connection.
4. `st.dataframe(rows)` draws the table.

When you edit a file, Streamlit offers a "Rerun" button (or can be set to rerun automatically). Refresh the browser to see the result.

## 4. The connection pool

Opening a database connection is slow, and Postgres can only handle a limited number. A **connection pool** opens a few connections once and lends them out. When code is done, the connection goes back for the next request. With several users at once, the pool caps the total number of connections and makes extra requests wait their turn.

We use `psycopg_pool.ConnectionPool`. Code borrows a connection with a `with` block:

```python
from adamfit.db import get_connection

with get_connection() as conn:
    conn.execute("UPDATE exercise SET muscle_group = %s WHERE exercise_id = %s", ("Back", 3))
```

When the block finishes normally the changes are **committed**. If an error occurs they are **rolled back**. Either way the connection returns to the pool. For plain reads, use `fetch_all(query, params)`, which does this for you.

### Why the pool is created in `db.py`, not `app.py`
`get_pool()` in `db.py` is decorated with `@st.cache_resource`. The first code that needs the pool creates it. Every later call, from any page, rerun or user, gets the same one. Keeping it in `db.py` means every module that needs the database (pages, `auth.py`, the `adamfit-create-user` command) just imports from one place, without depending on `app.py` having set anything up.

### Settings
Set these in the root `.env`. They have defaults, so all are optional. **Restart Streamlit after changing them**, because the pool is cached.

| Variable | Meaning | Default |
|----------|---------|---------|
| `DB_POOL_MIN_SIZE` | Connections kept open at all times | 1 |
| `DB_POOL_MAX_SIZE` | Most connections that may be open at once | 10 |
| `DB_POOL_TIMEOUT` | Seconds a request waits for a free connection before failing | 30 |
| `DB_POOL_MAX_IDLE` | Seconds before extra idle connections are closed | 600 |
| `DB_POOL_MAX_LIFETIME` | Seconds before any connection is replaced with a fresh one | 3600 |

Keep `DB_POOL_MAX_SIZE` well below Postgres's `max_connections` (100 by default).
