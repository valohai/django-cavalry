import traceback

from django.db.backends.utils import logger

from cavalry.locals import get_storage
from cavalry.stack import Stack


def record(*, db, duration, params, sql, times=None, error=None):
    if get_storage().get('db_record_stacks'):
        # The two last frames are in cavalry, so slice them off
        stack = Stack(traceback.extract_stack()[:-2])
    else:
        stack = []
    db.queries_log.append(
        {
            'sql': (f'{times} times: {sql}' if times else sql),
            'time': f"{duration:.3f}",
            'hrtime': duration,
            'stack': stack,
            'error': error,
        }
    )
    logger.debug(
        '(%.3f) %s; args=%s',
        duration,
        sql,
        params,
        extra={'duration': duration, 'sql': sql, 'params': params},
    )
