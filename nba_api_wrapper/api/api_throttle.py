import time

class APIThrottle:
    def __init__(self, interval_seconds, max_calls_per_interval):
        self.interval_seconds = interval_seconds
        self.max_calls_per_interval = max_calls_per_interval
        self._interval_begin_time = None
        self._interval_counts = 0

    def __call__(self, func):
        def wrapper(instance, *args, **kwargs):
            self._api_calls_counter()
            return func(instance, *args, **kwargs)

        return wrapper

    def _api_calls_counter(self):
        current_time = time.time()

        if self._interval_begin_time is None:
            self._interval_counts = 1
            self._interval_begin_time = current_time
            return

        if current_time - self._interval_begin_time < self.interval_seconds:
            self._interval_counts += 1
            if self._interval_counts > self.max_calls_per_interval:
                sleep_seconds = 60 - (current_time - self._interval_begin_time)
                time.sleep(sleep_seconds)
                self._interval_counts = 0
                self._interval_begin_time = time.time()