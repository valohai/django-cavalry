from contextlib import contextmanager

import django
from django.db import connections
from django.db.backends import utils as db_backend_utils
from django.db.backends.utils import CursorWrapper

from cavalry.db_common import record
from cavalry.timing import get_time

assert django.VERSION[0] == 2, "This module won't work with Django 3"

DefaultCursorDebugWrapper = db_backend_utils.CursorDebugWrapper


class CavalryCursorDebugWrapper(CursorWrapper):
    # This is an enhanced version of `django.db.backends.utils.CursorDebugWrapper`.

    def execute(self, sql, params=None):
        start = get_time()
        try:
            return super().execute(sql, params)
        finally:
            stop = get_time()
            duration = stop - start
            sql = self.db.ops.last_executed_query(self.cursor, sql, params)
            self._record(sql, params, duration)

    def executemany(self, sql, param_list):
        start = get_time()
        try:
            return super().executemany(sql, param_list)
        finally:
            stop = get_time()
            duration = stop - start
            try:
                times = len(param_list)
            except TypeError:  # param_list could be an iterator
                times = '?'
            self._record(sql, param_list, duration, times)

    def _record(self, sql: str, params, duration: float, times=None):
        record(db=self.db, sql=sql, params=params, duration=duration, times=times)


@contextmanager
def enable_db_tracing():
    for conn in connections.all():
        db_backend_utils.CursorDebugWrapper = CavalryCursorDebugWrapper
        conn._cavalry_old_force_debug_cursor = conn.force_debug_cursor
        conn.force_debug_cursor = True
    yield
    for conn in connections.all():
        conn.force_debug_cursor = conn._cavalry_old_force_debug_cursor
        db_backend_utils.CursorDebugWrapper = DefaultCursorDebugWrapper
