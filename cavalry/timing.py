import time

try:
    assert time.perf_counter()
    get_time = time.perf_counter
except:
    get_time = time.time
