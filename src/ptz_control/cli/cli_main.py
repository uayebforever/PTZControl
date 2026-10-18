import argparse
import logging
import sys
from typing import List

from .exit_codes import ExitCode
from .. import log_config
from ..exceptions import ApplicationError, UserError

log = logging.getLogger(__name__)


def main() -> int:
    try:
        return main_with_args(sys.argv[1:]).value
    except KeyboardInterrupt:
        print("Ctrl-C received: Exiting...", file=sys.stderr)
        return ExitCode.USER_INTERRUPT.value


def main_with_args(unparsed_arguments: List[str]) -> ExitCode:
    args = _parse_args(unparsed_arguments)
    _configure_logging(args)

    try:
        from ..gui.app import run as run_gui

        run_gui()
    except UserError as err:
        print("User error: " + str(err), file=sys.stderr)
        return ExitCode.USER_ERROR
    except ApplicationError as err:
        print("Application error: " + str(err), file=sys.stderr)
        return ExitCode.APPLICATION_ERROR
    except Exception as exception:
        log.exception("Unexpected error!", exc_info=exception)
        print("Unexpected error: " + str(exception), file=sys.stderr)
        return ExitCode.UNEXPECTED_ERROR

    return ExitCode.OK


def _configure_logging(args: argparse.Namespace) -> None:
    log_config.configure_logging(log_config.LogLevel.ON if args.debug else log_config.LogLevel.OFF)
    log.info("Parsed CLI arguments: %s", args)


def _parse_args(unparsed_arguments: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="ptz-control", exit_on_error=False)
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging to the console and to ptz-control.log.",
    )
    return parser.parse_args(unparsed_arguments)
