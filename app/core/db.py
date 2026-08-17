from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from app.core.config import get_database_config


@contextmanager
def get_connection() -> Iterator[Connection]:
    config = get_database_config()
    with psycopg.connect(config.url, row_factory=dict_row) as conn:
        yield conn
