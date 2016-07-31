"""Process check based on CPU usage.
"""

import psutil
import time

from supervisor_checks import errors
from supervisor_checks.check_modules import base

__author__ = 'vovanec@gmail.com'


PSUTIL_CHECK_INTERVAL = 3.0
DEF_CPU_CHECK_INTERVAL = 3600


class CPUCheck(base.BaseCheck):
    """Process check based on CPU usage.
    """

    NAME = 'cpu'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._first_seen_over_threshold = float('inf')
        self._over_threshold = False
        self._check_interval = self._config.get(
            'interval', DEF_CPU_CHECK_INTERVAL)

    def __call__(self, process_spec):

        pid = process_spec['pid']
        process_name = process_spec['name']

        cpu_pct = self._get_cpu_percent(pid, process_name)
        self._log('CPU percent used by process %s is %s%%',
                  process_name, cpu_pct)

        if cpu_pct > self._config['max_cpu']:
            if (time.time() - self._first_seen_over_threshold >
                    self._check_interval):

                self._log('CPU usage for process %s was above the configured '
                          'threshold %s%% for %s seconds.',
                          process_name, self._config['max_cpu'],
                          self._check_interval)

                return False
            elif not self._over_threshold:
                self._log('CPU usage for process %s is above the threshold '
                          '%s%%.', process_name, self._config['max_cpu'],)
                self._first_seen_over_threshold = time.time()
                self._over_threshold = True
        else:
            if self._over_threshold:
                self._log('CPU usage for process %s dropped below the '
                          'threshold %s%% after %s seconds.', process_name,
                          self._config['max_cpu'],  self._check_interval)

            self._first_seen_over_threshold = float('inf')
            self._over_threshold = False

        return True

    def _get_cpu_percent(self, pid, process_name):
        """Get CPU percent used by process.
        """

        self._log('Checking for CPU percent used by process %s.', process_name)

        return psutil.Process(pid).cpu_percent()

    def _validate_config(self):

        if 'max_cpu' not in self._config:
            raise errors.InvalidCheckConfig(
                'Required `max_cpu` parameter is missing in %s check config.'
                % (self.NAME,))

        if not isinstance(self._config['max_cpu'], (int, float)):
            raise errors.InvalidCheckConfig(
                '`max_cpu` parameter must be numeric type in %s check config.'
                % (self.NAME,))
