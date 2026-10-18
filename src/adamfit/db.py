"""Database access helpers built on psycopg 3 and a shared connection pool."""

import os

import streamlit as st
from dotenv import load_dotenv
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

load_dotenv()


def _env_int(name: str, default: int) -> int:
    """
    Read an integer setting from an environment variable.

    Parameters
    ----------
    name : str
        Name of the environment variable.
    default : int
        Value to use when the variable is missing or empty.

    Returns
    -------
    int
        The variable's value as an integer, or ``default``.
    """
    value = os.environ.get(name, "").strip()
    return int(value) if value else default


@st.cache_resource
def get_pool() -> ConnectionPool:
    """
    Return the shared database connection pool, creating it on first use.

    ``st.cache_resource`` keeps one pool for the whole Streamlit server, so
    every page, rerun and user session shares it. Connection details come from
    the DB_* variables in the project .env file, and pool sizing from the
    DB_POOL_* variables (see ``.env.example``). Restart Streamlit after
    changing them.

    Returns
    -------
    ConnectionPool
        An open pool whose connections return rows as dictionaries.
    """
    conninfo = (
        f"host={os.environ['DB_HOST']} port={os.environ['DB_PORT']} "
        f"dbname={os.environ['DB_NAME']} user={os.environ['DB_USER']} "
        f"password={os.environ['DB_PASSWORD']}"
    )
    return ConnectionPool(
        conninfo,
        min_size=_env_int("DB_POOL_MIN_SIZE", 1),
        max_size=_env_int("DB_POOL_MAX_SIZE", 10),
        timeout=_env_int("DB_POOL_TIMEOUT", 30),
        max_idle=_env_int("DB_POOL_MAX_IDLE", 600),
        max_lifetime=_env_int("DB_POOL_MAX_LIFETIME", 3600),
        kwargs={"row_factory": dict_row},
        check=ConnectionPool.check_connection,
        open=True,
    )


def get_connection():
    """
    Borrow a connection from the pool for use in a ``with`` block.

    The connection is committed when the block succeeds, rolled back if it
    raises, and returned to the pool either way.

    Returns
    -------
    contextlib.AbstractContextManager[Connection]
        Use as ``with get_connection() as conn:``.
    """
    return get_pool().connection()


def fetch_all(query: str, params: tuple | None = None) -> list[dict]:
    """
    Run a SELECT query and return every row.

    Parameters
    ----------
    query : str
        SQL to run. Use ``%s`` placeholders for values.
    params : tuple | None, optional
        Values for the placeholders in ``query``.

    Returns
    -------
    list[dict]
        One dictionary per row, keyed by column name.
    """
    with get_connection() as conn:
        return conn.execute(query, params).fetchall()
