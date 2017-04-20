"""Process check based on HTTP query.
"""

import base64

from supervisor_checks import errors
from supervisor_checks import utils
from supervisor_checks.check_modules import base
from supervisor_checks.compat import httplib

__author__ = 'vovanec@gmail.com'


DEFAULT_RETRIES = 2
DEFAULT_TIMEOUT = 15


class HTTPCheck(base.BaseCheck):
    """Process check based on HTTP query.
    """

    HEADERS = {'User-Agent': 'http_check'}
    NAME = 'http'

    def __call__(self, process_spec):

        try:
            port = utils.get_port(self._config['port'], process_spec['name'])
            return self._http_check(process_spec['name'], port)
        except errors.InvalidPortSpec:
            self._log('ERROR: Could not extract the HTTP port for process '
                      'name %s using port specification %s.',
                      process_spec['name'], self._config['port'])

            return True
        except Exception as exc:
            self._log('Check failed: %s', exc)

        return False

    def _http_check(self, process_name, port):

        self._log('Querying URL http://localips:%s%s for process %s',
                  port, self._config['url'],
                  process_name)

        num_retries = self._config.get('num_retries', DEFAULT_RETRIES)
        timeout = self._config.get('timeout', DEFAULT_TIMEOUT)
        username = self._config.get('username')
        password = self._config.get('password')

        with utils.retry_errors(num_retries, self._log).retry_context(
                self._make_http_request) as retry_http_request:
            res = retry_http_request(
                port, timeout, username=username, password=password)

        self._log('Status contacting URL http://localip:%s%s for process %s: '
                  '%s %s' % (port, self._config['url'], process_name,
                             res.status, res.reason))

        if res.status != httplib.OK:
            raise httplib.HTTPException(
                'Bad HTTP status code: %s' % (res.status,))

        return True

    def _make_http_request(self, port, timeout,
                           username=None, password=None):

        headers = self.HEADERS.copy()

        if username and password:
            auth_str = '%s:%s' % (username, password)
            headers['Authorization'] = 'Basic %s' % base64.b64encode(
                auth_str.encode()).decode()

        for ip in utils.get_local_ip():
            host_port = '%s:%s' % (ip, port,) 
            connection = httplib.HTTPConnection(host_port, timeout=timeout)
            try:
                connection.request('GET', self._config['url'], headers=headers)
                return connection.getresponse()
            except:
                pass

        return False


    def _validate_config(self):

        if 'url' not in self._config:
            raise errors.InvalidCheckConfig(
                'Required `url` parameter is missing in %s check config.' % (
                    self.NAME,))

        if not isinstance(self._config['url'], str):
            raise errors.InvalidCheckConfig(
                '`url` parameter must be string type in %s check config.' % (
                    self.NAME,))

        if 'port' not in self._config:
            raise errors.InvalidCheckConfig(
                'Required `port` parameter is missing in %s check config.' % (
                    self.NAME,))
