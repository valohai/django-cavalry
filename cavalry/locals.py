from contextlib import contextmanager
from threading import local

_storage = local()


@contextmanager
def managed(**kwargs):
    _storage.data = dict(**kwargs)
    yield _storage.data
    del _storage.data


def get_storage() -> dict:
    return getattr(_storage, 'data', {})
