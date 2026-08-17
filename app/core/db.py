from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from app.core.config import get_database_config

MIGRATION_COMMAND = "uv run alembic upgrade head"


@contextmanager
def get_connection() -> Iterator[Connection]:
    config = get_database_config()
    with psycopg.connect(config.url, row_factory=dict_row) as conn:
        yield conn


def check_required_tables(conn: Connection, worker: str, required_tables: set[str]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "select table_name, to_regclass(table_name) is not null as exists "
            "from unnest(%s::text[]) as table_name",
            (sorted(required_tables),),
        )
        missing = sorted(row["table_name"] for row in cur.fetchall() if not row["exists"])

    if missing:
        tables = ", ".join(missing)
        raise RuntimeError(
            f"Database schema for {worker} is missing required tables: {tables}. "
            f"Run `{MIGRATION_COMMAND}` from idx-stock-backend."
        )
