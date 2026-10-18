from argparse import ArgumentParser

from ptz_control import __version__ as package_version
from .command import Command


class VersionCommand(Command):
    name = "version"
    help = "Print version information"

    def configure_arg_parser(self, parser: ArgumentParser) -> None:
        # No arguments
        pass

    def execute(self, args):
        print_version()


def print_version():
    print(f"ptz_control version: {package_version}")
