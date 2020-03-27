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


class PredictionTable:
    __slots__ = ["table"]

    def __init__(self):
        from texttable import Texttable

        self.table = Texttable()
        self.table.set_deco(Texttable.HEADER | Texttable.HLINES)
        self.table.set_cols_dtype(["t", "t", "t", "t", "t"])
        self.table.set_cols_align(["c", "r", "r", "r", "l"])
        self.table.set_cols_valign(["t", "t", "t", "t", "m"])
        self.table.header([_("H"), _("PRESSURE"), _("ALT"), _("ALT/hr"), ""])
        self.table.set_cols_width([5, 11, 7, 6, 38])  # total width = 80 (with added borders)

    def _add(self, hour: str, pressure: str, alt: str = "", alt_h: str = "", times: str = ""):
        return self.table.add_row([hour, pressure, alt, alt_h, times])

    def add_start(self, hour: int, minute: int, pressure: float, times: iter):
        _h = "{:d}h{:02d}".format(int(hour), int(minute))
        _p = "{:.2f} hPa".format(float(pressure))
        _t = ", ".join(times)

        return self._add(hour=_h, pressure=_p, times=_t)

    def add(self, hour: int, pressure: float, alt: float, alt_h: float, times: iter) -> int:
        _h = "{:d}h".format(int(hour))
        _p = "{:.2f} hPa".format(pressure) if type(pressure) is float else ""
        _a = "{:.1f}m".format(alt) if type(alt) is float else ""
        _ah = "{:.1f}m".format(alt_h) if type(alt) is float else ""
        _t = ", ".join(times)

        return self._add(hour=_h, pressure=_p, alt=_a, alt_h=_ah, times=_t)

    def display_table(self):
        return self.table.draw()
