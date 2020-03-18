#! python3
"""
MIT License

Copyright (c) 2020 Walter Wlodarski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import argparse
import sys
from pathlib import Path


class CommandLineParser:
    def __init__(self, prog_path: Path, description: str, shortname: str, version: str):
        self.parser = argparse.ArgumentParser(
            prog=prog_path.name, description=description, epilog="{}, version {}".format(shortname, version),
        )

        self.parser.add_argument(
            "-n", "--no-key", action="store_true", help='disable "Press any key to continue"',
        )
        self.parser.add_argument("-s", "--slack", help="Slack channel")
        self.parser.add_argument("--latitude", help="latitude", type=float)
        self.parser.add_argument("--longitude", help="longitude", type=float)
        self.parser.add_argument("--override-url", help="specific weather station URL", type=str)

        self.bundle_dir = Path(getattr(sys, "_MEIPASS", prog_path.parent))  # for pyinstalle
        self.localedir = self.bundle_dir.joinpath("locales")
        self.all_lang = [d.name for d in self.localedir.iterdir() if d.is_dir()]

        self.parser.add_argument("--lang", help="interface language ({})".format(", ".join(self.all_lang)))
        self.parser.add_argument(
            "-v", "--verbose", action="store_true", help="include details about the polynomial model",
        )

        self.args = self.parser.parse_args()

    def link_together(self, var_a, var_b, errmsg):
        if (var_a is not None and var_b is None) or (var_a is None and var_b is not None):
            self.parser.error(errmsg)
