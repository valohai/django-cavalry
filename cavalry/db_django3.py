from contextlib import contextmanager

import django
from django.db import connection

from cavalry.db_common import record
from cavalry.timing import get_time

assert django.VERSION[0] != 2, "This module won't work with Django 2"


def log_query(execute, sql, params, many, context):
    db = context['connection']
    start = get_time()
    error = None
    try:
        result = execute(sql, params, many, context)
    except Exception as e:
        error = str(e)
        raise
    else:
        return result
    finally:
        duration = get_time() - start
        record(db=db, sql=sql, params=params, duration=duration, error=error)


@contextmanager
def enable_db_tracing():
    with connection.execute_wrapper(log_query):
        yield
