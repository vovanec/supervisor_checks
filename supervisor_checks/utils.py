"""Utility functions.
"""


import contextlib
import functools
import re
import time
import os
import tempfile

from supervisor_checks import errors

__author__ = 'vovanec@gmail.com'


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

        :param func: decorated function.
        """

        yield self(func)


def get_port(port_or_port_re, process_name):
    """Given the regular expression, extract port from the process name.

    :param str port_or_port_re: whether integer port or port regular expression.
    :param str process_name: process name.

    :rtype: int|None
    """

    if isinstance(port_or_port_re, int):
        return port_or_port_re

    try:
        return int(port_or_port_re)
    except ValueError:
        pass

    match = re.match(port_or_port_re, process_name)

    if match:
        try:
            groups = match.groups()
            if len(groups) == 1:
                return int(groups[0])
        except (ValueError, TypeError) as err:
            raise errors.InvalidCheckConfig(err)

    raise errors.InvalidCheckConfig(
        'Could not extract port number for process name %s using regular '
        'expression %s' % (process_name, port_or_port_re))




# Directly copied from the tempfile module
class _TemporaryFileCloser:
    """A separate object allowing proper closing of a temporary file's
    underlying file object, without adding a __del__ method to the
    temporary file."""

    file = None  # Set here since __del__ checks it
    close_called = False

    def __init__(self, file, name, delete=True):
        self.file = file
        self.name = name
        self.delete = delete

    # NT provides delete-on-close as a primitive, so we don't need
    # the wrapper to do anything special.  We still use it so that
    # file.name is useful (i.e. not "(fdopen)") with NamedTemporaryFile.
    if os.name != 'nt':
        # Cache the unlinker so we don't get spurious errors at
        # shutdown when the module-level "os" is None'd out.  Note
        # that this must be referenced as self.unlink, because the
        # name TemporaryFileWrapper may also get None'd out before
        # __del__ is called.

        def close(self, unlink=os.unlink):
            if not self.close_called and self.file is not None:
                self.close_called = True
                try:
                    self.file.close()
                finally:
                    if self.delete:
                        unlink(self.name)

        # Need to ensure the file is deleted on __del__
        def __del__(self):
            self.close()

    else:
        def close(self):
            if not self.close_called:
                self.close_called = True
                self.file.close()


# Directly copied from the tempfile module
class _TemporaryFileWrapper:
    """Temporary file wrapper

    This class provides a wrapper around files opened for
    temporary use.  In particular, it seeks to automatically
    remove the file when it is no longer needed.
    """

    def __init__(self, file, name, delete=True):
        self.file = file
        self.name = name
        self.delete = delete
        self._closer = _TemporaryFileCloser(file, name, delete)

    def __getattr__(self, name):
        # Attribute lookups are delegated to the underlying file
        # and cached for non-numeric results
        # (i.e. methods are cached, closed and friends are not)
        file = self.__dict__['file']
        a = getattr(file, name)
        if hasattr(a, '__call__'):
            func = a
            @functools.wraps(func)
            def func_wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            # Avoid closing the file as long as the wrapper is alive,
            # see issue #18879.
            func_wrapper._closer = self._closer
            a = func_wrapper
        if not isinstance(a, int):
            setattr(self, name, a)
        return a

    # The underlying __enter__ method returns the wrong object
    # (self.file) so override it to return the wrapper
    def __enter__(self):
        self.file.__enter__()
        return self

    # Need to trap __exit__ as well to ensure the file gets
    # deleted when used in a with statement
    def __exit__(self, exc, value, tb):
        result = self.file.__exit__(exc, value, tb)
        self.close()
        return result

    def close(self):
        """
        Close the temporary file, possibly deleting it.
        """
        self._closer.close()

    # iter() doesn't use __getattr__ to find the __iter__ method
    def __iter__(self):
        # Don't return iter(self.file), but yield from it to avoid closing
        # file as long as it's being used as iterator (see issue #23700).  We
        # can't use 'yield from' here because iter(file) returns the file
        # object itself, which has a close method, and thus the file would get
        # closed when the generator is finalized, due to PEP380 semantics.
        for line in self.file:
            yield line


class NotificationFile:
    @staticmethod
    def get_tempdir():
        return os.path.join(tempfile.gettempdir(), "supervisor_checks")


    @staticmethod
    def get_filename(process_group, process_name, pid):
        return f"{process_group!s}-{process_name!s}-{pid!s}"

    @staticmethod
    def get_filepath(process_group, process_name, pid):
        return os.path.join(NotificationFile.get_tempdir(), NotificationFile.get_filename(process_group, process_name, pid))

    @staticmethod
    def get_filepath_within_subprocess():
        return os.path.join(NotificationFile.get_tempdir(), NotificationFile.get_filename(os.getenv("SUPERVISOR_GROUP_NAME"), os.getenv("SUPERVISOR_PROCESS_NAME"), os.getpid()))

    def __init__(self, filepath=None, delete=True):
        """
        Creates a NotificationFile object used to indicate a heartbeat.

        param str filepath: optional filepath to use as notification file
        param bool delete: wether to delete the notification file after fd is closed 
        """
        if filepath is None:
            if not os.path.exists(self.get_tempdir()):
                os.mkdir(self.get_tempdir())
            filepath = self.get_filepath_within_subprocess()

        def opener(file, flags):
            flags |= os.O_NOFOLLOW
            flags |= os.O_CREAT
            return os.open(file, flags, mode=0o000)

        fd = open(filepath, "rb", buffering=0, opener=opener)
        self._tmp = _TemporaryFileWrapper(fd, filepath, delete=delete)

        self.spinner = 0

    def notify(self):
        self.spinner = (self.spinner + 1) % 2
        os.fchmod(self._tmp.fileno(), self.spinner)

    def close(self):
        return self._tmp.close()
