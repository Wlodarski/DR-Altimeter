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
from datetime import datetime

from ISA import AtmosphericPressure, InternationalStandardAtmosphere


class Forecast:
    def __init__(self):
        self.values = []

    def add(self, time: datetime, pressure: AtmosphericPressure) -> None:
        self.values.append({"time": time, "pressure": AtmosphericPressure(hectopascal=pressure)})

    def get(self, key: str):
        return [_point[key] for _point in self.values]

    def pressures(self):
        return [_i.value for _i in self.get("pressure")]

    def altitudes(self) -> float:
        _isa = InternationalStandardAtmosphere()
        return [_isa.altitude(i.value) for i in self.get("pressure")]

    def delta_altitudes(self, p_ref):
        _isa = InternationalStandardAtmosphere()
        return [_isa.delta_altitude(p_ref=p_ref, current_p=i.value) for i in self.get("pressure")]

    def times(self):
        return self.get("time")

    @staticmethod
    def cross_platform(s, c="#"):
        return s.replace(c + "0", c).replace(c, "")

    def formatted_times(self, fmt, c="#") -> str:
        return [self.cross_platform(i.strftime(fmt), c) for i in self.times()]

    def sorted_by(self, key, reverse=False) -> bytearray:
        return sorted(self.values, key=lambda _i: _i[key], reverse=reverse)

    def reorder_chronologically(self, reverse=False) -> bytearray:
        self.values = self.sorted_by("time", reverse)
