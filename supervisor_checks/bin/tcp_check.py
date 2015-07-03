"""Example configuration:

[eventlistener:example_check]
command=/usr/local/bin/supervisor_tcp_check -n example_service_check -u /ping -t 30 -r 3 -g example_service
events=TICK_60
"""

__author__ = 'vovanec@gmail.net'


import argparse
import sys

from monitoring.supervisord import check_runner
from monitoring.supervisord.checks import tcp


def _make_argument_parser():
    """Create the option parser.
    """

    parser = argparse.ArgumentParser(
        description='Run TCP check program.')
    parser.add_argument('-n', '--check-name', dest='check_name',
                        type=str, required=True, default=None,
                        help='Check name.')
    parser.add_argument('-g', '--process-group', dest='process_group',
                        type=str, required=True, default=None,
                        help='Supervisor process group name.')
    parser.add_argument(
        '-t', '--timeout', dest='timeout', type=int, required=False,
        default=tcp.DEFAULT_TIMEOUT,
        help='Connection timeout. Default: %s' % (tcp.DEFAULT_TIMEOUT,))
    parser.add_argument(
        '-r', '--num-retries', dest='num_retries', type=int,
        default=tcp.DEFAULT_RETRIES,  required=False,
        help='Connection retries. Default: %s' % (tcp.DEFAULT_RETRIES,))
    parser.add_argument(
        '-p', '--port', dest='port', type=int,
        default=None, required=False, help='TCP port to query.')

    return parser


def main():

    arg_parser = _make_argument_parser()
    args = arg_parser.parse_args()

    checks_config = [(tcp.TCPCheck, {'timeout': args.timeout,
                                     'num_retries': args.num_retries,
                                     'port': args.port})]

    return check_runner.CheckRunner(
        args.check_name, args.process_group, checks_config).run()


if __name__ == '__main__':

    sys.exit(main())
