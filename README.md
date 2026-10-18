# AdamFit

A personal fitness web app: Streamlit front end, PostgreSQL 18 back end (Docker), psycopg 3, golang-migrate.

## Prerequisites
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop (running)

## 1. Configure environment files
Both `.env` files are git-ignored. Copy the examples and fill them in.

```bash
cp .env.example .env
cp database/.env.example database/.env
```

- `database/.env`: `POSTGRES_PASSWORD` (superuser), `MASTER_USR_PASSWORD` (app user), `POSTGRES_PORT`.
- `.env`: `DB_PASSWORD` must equal `MASTER_USR_PASSWORD`. `DB_USER` stays `master_usr`.

## 2. Start the database
```bash
cd database
docker compose up -d --build
docker compose ps        # wait until db is "healthy"
```

On the first start with an empty volume, `setup_scripts/init.sh` runs the SQL in `database/shared_dir/` to create the `fitness` database, the `fit` schema, the `master` role and the `master_usr` user.

Data persists in the `adamfit_pgdata` Docker volume across `down` and `up`.

## 3. Run migrations
```bash
cd database
docker compose run --rm migrate up          # apply all
docker compose run --rm migrate down 1      # roll back one
```

## 4. Run the app
From the project root:
```bash
uv sync
uv run streamlit run src/adamfit/app.py
```
Open http://localhost:8501. The home page should show "Connected to the database", and the Exercises page should list the dummy data.

## Stopping and resetting
```bash
cd database
docker compose down        # stop, keep data
docker compose down -v     # stop and DELETE all data (initial setup re-runs next start)
```
Changes to the initial setup scripts only take effect after `down -v`.

## Project docs
- `instructions.md`: guidance for AI assistants (also referenced by `CLAUDE.md` and `.github/copilot-instructions.md`)
- `docs/streamlit_basics.md`: how Streamlit works, how the code is organized, and the connection pool settings (`DB_POOL_*` in `.env`)
- `docs/`: one markdown file per UI page
