"""Utility functions.
"""

__author__ = 'vovanec@gmail.com'


import contextlib
import functools
import time


RETRY_SLEEP_TIME = 3


class retry_errors(object):
    """Decorator to retry on errors.
    """

    def __init__(self, num_retries, log):

        self._num_retries = num_retries
        self._log = log

    def __call__(self, func):

        @functools.wraps(func)
        def wrap_it(*args, **kwargs):
            tries_count = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    tries_count += 1

                    if tries_count <= self._num_retries:
                        retry_in = tries_count * RETRY_SLEEP_TIME
                        self._log(
                            'Exception occurred: %s. Retry in %s seconds.' % (
                                exc, retry_in))

                        time.sleep(retry_in)
                    else:
                        raise

        return wrap_it

    @contextlib.contextmanager
    def retry_context(self, func):
        """Use retry_errors object as a context manager.
        """

        yield self(func)
