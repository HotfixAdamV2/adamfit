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

### Multipage apps
The file you pass to `streamlit run` (`app.py`) is the home page. Every Python file in a `pages/` folder beside it becomes its own page in the sidebar, named after the file. **Each page is a separate script**, and someone can open a page's URL directly without ever visiting the home page.

## 2. How AdamFit is organized

| Path | What lives there |
|------|------------------|
| `src/adamfit/app.py` | The entry point and Home page |
| `src/adamfit/pages/` | One file per additional page (for example `exercises.py`) |
| `src/adamfit/db.py` | Everything about talking to the database: the connection pool and query helpers |
| `docs/` | One markdown file per page (`*_page.md`) and this guide |
| `docs/widgets/` | One short explanation per Streamlit widget, shared by all pages |
| `database/` | Docker setup for Postgres, setup SQL, and `migrations/` that build the tables |
| `.env` | Settings for the app (database login, pool sizes). Never committed |
| `instructions.md`, `.claude/` | Guidance, skills and agents for AI assistants |

The path of one request:

```
Browser -> page script (pages/exercises.py) -> db.py (fetch_all) -> connection pool -> Postgres
```

## 3. How to start reading the code
Read in this order:

1. [README.md](../README.md): how to run everything.
2. `src/adamfit/app.py`: the smallest page. Short and top-to-bottom.
3. `src/adamfit/db.py`: how the database is reached.
4. `src/adamfit/pages/exercises.py`: a page that reads from the database.
5. The matching page doc ([home](home_page.md), [exercises](exercises_page.md)): explains each step with snippets.
6. Widget docs in [widgets/](widgets/README.md): look up anything like `st.dataframe` you don't recognize.
7. `database/migrations/`: how the `exercise` table the page reads is created.

**Follow one example:** open the Exercises page.
1. Streamlit runs `pages/exercises.py` from the top.
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
`get_pool()` in `db.py` is decorated with `@st.cache_resource`. The first page that needs the pool creates it. Every later call, from any page, rerun or user, gets the same one. Because pages can be opened directly, we cannot rely on `app.py` having run first. `app.py` still calls `get_pool()` once so the pool is ready as soon as the Home page loads.

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
