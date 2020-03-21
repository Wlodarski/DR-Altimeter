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

from abc import abstractmethod

import matplotlib.dates as mdates
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle
from matplotlib.ticker import MultipleLocator, FormatStrFormatter, NullFormatter
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from utils import cross_platform_leading_zeros_removal as no_leading_zeros


class MyDateFormatter(mdates.DateFormatter):
    def __init__(self, fmt: str, tz=None):
        mdates.DateFormatter.__init__(self, fmt, tz)

    def __call__(self, x, pos=0):
        return no_leading_zeros(mdates.DateFormatter.__call__(self, x, pos))


class NoPanXAxes(Axes):
    """
    Defintion of a Matplotlib Projection that forbids any perpendicular (up/down) pan
    """

    name = "No Pan X Axes"

    @abstractmethod
    def drag_pan(self, button, key, _x, _y):
        Axes.drag_pan(self, button, "x", _x, _y)  # pretend key=='x'


class LinkedRectangles:
    """
    links two rectangles to two axes. Any zoom/pan propagates to the two rectangles
    """

    def __init__(self, ax1: Axes, r1: Rectangle, ax2: Axes, r2: Rectangle):
        self.r = [r1, r2]
        self.aa = [ax1, ax2]

    def update(self, *_):
        self.r[0].set_bounds(self.aa[0].viewLim.bounds)
        self.r[1].set_bounds(self.aa[1].viewLim.bounds)
        self.aa[0].figure.canvas.draw_idle()
        self.aa[1].figure.canvas.draw_idle()


class MyMatplotlibTools:
    def __init__(self):
        pass

    @staticmethod
    def viewport_lim(vector, end_index, start_index=0, corner1=None, corner2=None):
        corner = corner1

        # padding proportional to the variation of altitude
        padding = max(abs(vector[end_index] - vector[start_index]) // 10, 1)

        if vector[-1] > (vector[start_index] + 10):  # multiple of 10, just above maximum altitude
            down_lim = min(vector[:end_index]) - padding
            up_lim = round(max(vector[:end_index]) + 5, -1) + padding
        elif vector[-1] < (vector[start_index] - 10):  # multiple of 10, just below minimum altitude
            down_lim = round(min(vector[:end_index]) - 5, -1) - padding
            up_lim = max(vector[:end_index]) + padding
            corner = corner2
        else:  # multiple of 10, just below minimum altitude and just above maximum altitude
            down_lim = round(min(vector[:end_index]) - 5, -1) - padding
            up_lim = round(max(vector[:end_index]) + 5, -1) + padding

        if corner is not None:
            return down_lim, up_lim, corner
        else:
            return down_lim, up_lim

    def set_ylimits(self, ax, y, visible_hours):
        ax.set_ylim(self.viewport_lim(y, visible_hours))

    @staticmethod
    def set_grid(ax):
        ax.grid(which="major", axis="x", linewidth=0.75, linestyle="-", color="0.75")
        ax.grid(which="minor", axis="x", linewidth=0.25, linestyle="-", color="0.75")
        ax.grid(which="major", axis="y", linewidth=0.75, linestyle="-", color="0.75")
        ax.grid(which="minor", axis="y", linewidth=0.25, linestyle="-", color="0.75")

    @staticmethod
    def format_date_ticks(ax):
        # bug solved by patching .../site-packages/matplotlib/axis.py
        # ref: https://github.com/matplotlib/matplotlib/issues/15621

        ax.xaxis.set_major_locator(mdates.HourLocator())
        ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=range(0, 60, 10)))
        ax.xaxis.set_major_formatter(MyDateFormatter("#%Hh"))
        ax.yaxis.set_major_locator(MultipleLocator(base=5))
        ax.yaxis.set_minor_locator(MultipleLocator(base=1))
        ax.yaxis.set_major_formatter(FormatStrFormatter("%.0f m"))

        sax = ax.secondary_xaxis("top")
        sax.xaxis.set_major_locator(mdates.HourLocator())
        sax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=range(0, 60, 10)))
        sax.xaxis.set_major_formatter(MyDateFormatter("#%Hh"))

        return sax

    @staticmethod
    def format_altitude_tick(ax, shift):
        say = ax.secondary_yaxis("right", functions=(lambda a: shift + a, lambda a: a - shift))
        say.yaxis.set_major_locator(MultipleLocator(base=5))
        say.yaxis.set_major_formatter(FormatStrFormatter("%.0f m"))

        return say

    @staticmethod
    def create_inset(top, bottom, gridsys, lloc):
        inset = inset_axes(
            top,
            width="10%",
            height="{}%".format(10 * gridsys.get_height_ratios()[1]),
            bbox_transform=top.transAxes,  # relative axes coordinates
            bbox_to_anchor=(0.0, 0.0, 1, 1),  # relative axes coordinates
            loc=lloc,
        )
        rect = LinkedRectangles(
            top,
            Rectangle((0, 0), 0, 0, facecolor="None", edgecolor="red", linewidth=0.5),
            bottom,
            Rectangle((0, 0), 0, 0, facecolor="None", edgecolor="tab:blue", linewidth=0.5),
        )
        rect.r[0].set_bounds(*top.viewLim.bounds)

        inset.add_patch(rect.r[0])
        inset.xaxis.set_major_formatter(NullFormatter())
        inset.tick_params(
            axis="both",
            which="both",
            bottom=False,
            top=False,
            left=False,
            right=False,
            labelbottom=False,
            labeltop=False,
            labelleft=False,
            labelright=False,
        )
        inset.patch.set_alpha(0.8)
        inset.spines["bottom"].set_alpha(0.5)
        inset.spines["top"].set_alpha(0.5)
        inset.spines["left"].set_alpha(0.5)
        inset.spines["right"].set_alpha(0.5)

        return inset, rect

    @staticmethod
    def add_inset(top, bottom, rect, gridsys, lloc):
        inset = inset_axes(
            bottom,
            width="10%",
            height="{}%".format(10 * gridsys.get_height_ratios()[0]),
            bbox_transform=bottom.transAxes,  # relative axes coordinates
            bbox_to_anchor=(0.0, 0.0, 1, 1),  # relative axes coordinates
            loc=lloc,
        )
        rect.r[1].set_bounds(*bottom.viewLim.bounds)

        bottom.callbacks.connect("lim_changed", rect.update)
        bottom.callbacks.connect("ylim_changed", rect.update)
        top.callbacks.connect("xlim_changed", rect.update)
        top.callbacks.connect("ylim_changed", rect.update)

        inset.add_patch(rect.r[1])
        inset.xaxis.set_major_formatter(NullFormatter())
        inset.tick_params(
            axis="both",
            which="both",
            bottom=False,
            top=False,
            left=False,
            right=False,
            labelbottom=False,
            labeltop=False,
            labelleft=False,
            labelright=False,
        )

        inset.patch.set_alpha(0.5)
        inset.spines["bottom"].set_alpha(0.2)
        inset.spines["top"].set_alpha(0.2)
        inset.spines["left"].set_alpha(0.2)
        inset.spines["right"].set_alpha(0.2)

        return inset
