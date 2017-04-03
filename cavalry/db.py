import traceback
from contextlib import contextmanager

from django.db import connections
from django.db.backends import utils as db_backend_utils
from django.db.backends.utils import CursorWrapper, logger

from cavalry.locals import get_storage
from cavalry.stack import Stack
from cavalry.timing import get_time


class CavalryCursorDebugWrapper(CursorWrapper):
    # This is an enhanced version of `django.db.backends.utils.CursorDebugWrapper`.

    def execute(self, sql, params=None):
        start = get_time()
        try:
            return super(CavalryCursorDebugWrapper, self).execute(sql, params)
        finally:
            stop = get_time()
            duration = stop - start
            sql = self.db.ops.last_executed_query(self.cursor, sql, params)
            self._record(sql, params, duration)

    def executemany(self, sql, param_list):
        start = get_time()
        try:
            return super(CavalryCursorDebugWrapper, self).executemany(sql, param_list)
        finally:
            stop = get_time()
            duration = stop - start
            try:
                times = len(param_list)
            except TypeError:  # param_list could be an iterator
                times = '?'
            self._record(sql, param_list, duration, times)

    def _record(self, sql, params, duration, times=None):
        if get_storage().get('db_record_stacks'):
            stack = Stack(traceback.extract_stack()[:-2])  # the two last frames are in cavalry
        else:
            stack = []
        self.db.queries_log.append({
            'sql': ('%s times: %s' % (times, sql) if times else sql),
            'time': "%.3f" % duration,
            'hrtime': duration,
            'stack': stack,
        })
        logger.debug(
            '(%.3f) %s; args=%s', duration, sql, params,
            extra={'duration': duration, 'sql': sql, 'params': params}
        )


@contextmanager
def force_debug_cursor():
    for conn in connections.all():
        conn._cavalry_old_force_debug_cursor = conn.force_debug_cursor
        conn.force_debug_cursor = True
    yield
    for conn in connections.all():
        conn.force_debug_cursor = conn._cavalry_old_force_debug_cursor


def patch_db():
    db_backend_utils.CursorDebugWrapper = CavalryCursorDebugWrapper
