import argparse
import sys
from pathlib import Path


class CommandLineParser:
    def __init__(self, prog_path: Path, description: str, shortname: str, version: str):
        self.parser = argparse.ArgumentParser(prog=prog_path.name,
                                              description=description,
                                              epilog='{}, version {}'.format(shortname, version))

        self.parser.add_argument('-n', '--no-key', action='store_true', help='disable "Press any key to continue"')
        self.parser.add_argument('-s', '--slack', help='Slack channel')
        self.parser.add_argument('--latitude', help='latitude', type=float)
        self.parser.add_argument('--longitude', help='longitude', type=float)
        self.parser.add_argument('--override-url', help='specific weather station URL', type=str)

        self.bundle_dir = getattr(sys, '_MEIPASS', prog_path.parent)  # for pyinstalle
        self.localedir = self.bundle_dir.joinpath('locales')
        self.all_lang = [d.name for d in self.localedir.iterdir() if d.is_dir()]

        self.parser.add_argument('--lang', help='interface language ({})'.format(', '.join(self.all_lang)))
        self.parser.add_argument('-v', '--verbose', action='store_true',
                                 help='include details about the polynomial model')

        self.args = self.parser.parse_args()
