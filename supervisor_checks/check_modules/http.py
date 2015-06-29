"""Process check based on HTTP query.
"""

__author__ = 'vovanec@gmail.com'

import http.client
import time

from supervisor_checks.check_modules import base


DEFAULT_RETRIES = 2
DEFAULT_RETRY_SLEEP_TIME = 3
DEFAULT_TIMEOUT = 15

LOCALHOST = '127.0.0.1'


class HTTPCheck(base.BaseCheck):
    """Process check based on HTTP query.
    """

    HEADERS = {'User-Agent': 'http_check'}
    NAME = 'http'

    def __call__(self, process_spec):

        try:
            port = self._config.get('port')
            if not port:
                # If there's no port provided in config, we assume the port
                # name is the last part of process name in the process group.
                port = process_spec['name'].rsplit('_', 1)[1]

            self._log('Querying URL http://%s:%s%s for process %s',
                      LOCALHOST, port, self._config['url'],
                      process_spec['name'])

            return self._http_check(process_spec['name'], port)

        except IndexError:
            self._log('Could not extract the HTTP port from the process '
                      'name %s and no port specified in configuration.',
                      process_spec['name'])
        except Exception as exc:
            self._log('Check failed: %s', exc)

        return False

    def _http_check(self, process_name, port):

        host_port = '%s:%s' % (LOCALHOST, port,)

        res = self._make_http_request(process_name, host_port)

        self._log('Status contacting URL http://%s%s for process %s: '
                  '%s %s' % (host_port, self._config['url'], process_name,
                             res.status, res.reason))

        if res.status != http.client.OK:
            raise http.client.HTTPException(
                'Bad HTTP status code: %s' % (res.status,))

        return True

    def _make_http_request(self, process_name, host_port):

        tries_count = 0

        while True:
            try:
                connection = http.client.HTTPConnection(
                    host_port, timeout=self._config['timeout'])
                connection.request(
                    'GET', self._config['url'], headers=self.HEADERS)

                return connection.getresponse()
            except Exception as exc:
                tries_count += 1

                if tries_count <= self._config['num_retries']:
                    retry_in = tries_count * DEFAULT_RETRY_SLEEP_TIME
                    self._log(
                        'Exception occurred during HTTP request to http://%s%s '
                        'for process %s: %s. Retry in %s seconds.' % (
                            host_port, self._config['url'], process_name, exc,
                            retry_in))

                    time.sleep(retry_in)
                else:
                    raise
