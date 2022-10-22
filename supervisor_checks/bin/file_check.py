
import argparse
import sys

from supervisor_checks import check_runner
from supervisor_checks.check_modules import file


def _make_argument_parser():
    """Create the option parser.
    """

    parser = argparse.ArgumentParser(
        description='Run File check program.')
    parser.add_argument('-n', '--check-name', dest='check_name',
                        type=str, required=True, default=None,
                        help='Health check name.')
    parser.add_argument('-g', '--process-group', dest='process_group',
                        type=str, default=None,
                        help='Supervisor process group name.')
    parser.add_argument('-N', '--process-name', dest='process_name',
                        type=str, default=None,
                        help='Supervisor process name. Process group argument is ignored if this ' +
                             'is passed in')
    parser.add_argument(
        '-t', '--timeout', dest='timeout', type=int, required=True,
        help='Timeout in seconds after no file change a process is considered dead.')
    parser.add_argument("-x", "--fail-on-error", dest="fail_on_error", action="store_true", help="Fail the health check on any error.")
    parser.add_argument("-f", "--file", dest="file", type=str, default=None, help="Filepath of file to check (default: /tmp/supervisor_checks/%%(process_group)s-%%(process_name)s-%%(process_pid)s-*)")
    return parser


def main():

    arg_parser = _make_argument_parser()
    args = arg_parser.parse_args()

    checks_config = [(file.FileCheck, {'timeout': args.timeout, 'fail_on_error': args.fail_on_error, 'file': args.file})]
    return check_runner.CheckRunner(
        args.check_name, args.process_group, args.process_name, checks_config).run()


if __name__ == '__main__':

    sys.exit(main())
