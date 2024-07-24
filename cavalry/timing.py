import time

try:
    if not time.perf_counter():
        raise Exception()
    get_time = time.perf_counter
except Exception:
    get_time = time.time
