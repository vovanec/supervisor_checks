"""Base process check.
"""

__author__ = 'vovanec@gmail.com'


class BaseCheck(object):
    """Base process check.
    """

    NAME = None

    def __init__(self, check_config, log):
        """Constructor.

        :param dict check_config: implementation specific check config.
        :param (str) -> None log: logging function.
        """

        self._config = check_config
        self.__log = log

    def __call__(self, process_spec):
        """Run single check.

        :param dict process_spec: process specification dictionary as returned
               from SupervisorD API.

        :return: True is check succeeded, otherwise False.
        :rtype: bool
        """

        raise NotImplementedError

    def _log(self, msg, *args):
        """Log check message.

        :param str msg: log message.
        """

        self.__log('%s: %s' % (self.__class__.__name__, msg % args))
