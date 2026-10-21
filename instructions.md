# AdamFit Project Instructions

Single source of truth for AI assistants (Claude Code, GitHub Copilot). `CLAUDE.md` and `.github/copilot-instructions.md` both point here.

## Purpose
A personal fitness web app. It is also a learning project for agentic development, Streamlit and full-stack engineering, so keep code simple and explain non-obvious choices.

## Stack
- Streamlit front end (Python 3.14), packages managed with **uv**
- PostgreSQL 18 in Docker, accessed from Python with **psycopg 3**
- Schema migrations with golang-migrate (run through its Docker image)
- A Go API layer may come later. Do not add one unless asked.

## Layout
| Path | Contents |
|------|----------|
| `src/adamfit/` | Python and Streamlit code: `app.py` (router), `pages/`, `db.py` (pool + helpers), `auth.py`, one query module per table (`users.py`, `weights.py`, `foods.py`, `recipes.py`, `food_logs.py`, `google_health_connection.py`), `google_health.py` (Google Health API OAuth + sync, see `docs/google_health_setup.md`), `units.py`, `nutrition.py` (serving/macro maths), `ui.py`, `cli/` |
| `database/` | `docker-compose.yml`, `Dockerfile`, its own `.env` |
| `database/setup_scripts/` | Mounted into the container; `init.sh` runs once on first start |
| `database/shared_dir/` | Two-way shared folder; holds the initial-setup SQL files |
| `database/migrations/` | golang-migrate files (`NNNNNN_name.up.sql` / `.down.sql`) |
| `configs/` | Config files |
| `docs/` | Markdown documentation, one file per UI page |
| `.claude/skills/`, `.claude/agents/` | Repo-level skills and custom agents |

## Commands
- Install deps: `uv sync`; add a dep: `uv add <pkg>`
- Run app: `uv run streamlit run src/adamfit/app.py`
- Create a login user: `uv run adamfit-create-user <username>`
- Start DB: `cd database && docker compose up -d`
- Migrate: `cd database && docker compose run --rm migrate up` (use `down 1` to roll back one)
- New migration: create the next numbered `.up.sql` and `.down.sql` pair in `database/migrations/`

## Database rules
- The application connects as `master_usr`, which assumes the `master` role at login and has `fit` as its search path. The `public` schema is locked down. Never put objects in it.
- Migrations run as `master_usr`, so new objects are owned by `master`.
- The `master` role may create `TEMPORARY` tables (e.g. for staging data inside a migration). It cannot change database-level settings or grants; those go in `database/shared_dir/03_create_roles_and_security.sql` and must be applied once by hand as `postgres` on existing databases.
- Follow the SQL skills in `.claude/skills/` (`sql-formatting`, `sql-naming`, `sql-migrations`).
- Delegate database work to the `database-developer` agent.

## Python rules
- Every function and class needs a NumPy-style docstring with type hints (skill: `python-docstrings`).
- `app.py` is a router using `st.navigation`. New pages must be registered there with `st.Page`. Logged-out users only get the login page.
- Put SQL in a per-table module (e.g. `weights.py`), not in page files. Pages call those functions.
- The database stores body measurements in metric units (kg, cm). Convert for display with `units.py`. Food servings are the exception: they use any unit in the `serving_unit` lookup table (g, oz, cup, bar...), and are always shown in the food's own unit. The user's imperial/metric setting never applies to foods. `nutrition.py` handles the serving and macro maths.
- Auth: Argon2 hashes via `auth.py`, login state in `st.session_state["user_id"]`, no sign-up page. See `docs/authentication.md`.
- Delegate Python and Streamlit work to the `ui-developer` agent.
- Whenever a page is added or changed, write or update its markdown doc in `docs/` (skill: `page-documentation`).
- Database access goes through the shared connection pool in `src/adamfit/db.py`: use `fetch_all(...)` for reads, or `with get_connection() as conn:` for writes. Never open connections directly. Pool settings are `DB_POOL_*` in the root `.env`. See `docs/streamlit_basics.md`.
- Use psycopg parameter placeholders (`%s`). Never build SQL with string formatting of user input.

## Secrets
`.env` files are git-ignored. Commit only `.env.example`. Never print or commit passwords.
