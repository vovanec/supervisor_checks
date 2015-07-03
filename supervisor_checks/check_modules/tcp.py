"""Process check based on TCP connection status.
"""

__author__ = 'vovanec@gmail.com'

import socket

from supervisor_checks import utils
from supervisor_checks.check_modules import base


DEFAULT_RETRIES = 2
DEFAULT_RETRY_SLEEP_TIME = 3
DEFAULT_TIMEOUT = 15

LOCALHOST = '127.0.0.1'


class TCPCheck(base.BaseCheck):
    """Process check based on TCP connection status.
    """

    NAME = 'tcp'

    def __call__(self, process_spec):

        timeout = self._config.get('timeout', DEFAULT_TIMEOUT)
        num_retries = self._config.get('num_retries', DEFAULT_RETRIES)

        try:
            port = self._config.get('port')
            if not port:
                # If there's no port provided in config, we assume the port
                # name is the last part of process name in the process group.
                port = int(process_spec['name'].rsplit('_', 1)[1])

            self._log('Trying to connect to TCP port %s for process %s',
                      port, process_spec['name'])

            with utils.retry_errors(num_retries, self._log).retry_context(
                    self._tcp_check) as retry_tcp_check:
                return retry_tcp_check(process_spec['name'], port, timeout)

        except (IndexError, TypeError, ValueError):
            self._log('ERROR: Could not extract the TCP port from the process '
                      'name %s and no port specified in configuration.',
                      process_spec['name'])
            return True
        except Exception as exc:
            self._log('Check failed: %s', exc)

        return False

    def _tcp_check(self, process_name, port, timeout):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((LOCALHOST, port))
        sock.close()

        self._log('Successfully connected to TCP port %s for process %s',
                  port, process_name)

        return True
