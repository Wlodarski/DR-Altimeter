# import matplotlib.pyplot as plt
# import matplotlib.ticker as ticker
# import numpy as np
# from matplotlib.axes import Axes
# from matplotlib.gridspec import GridSpec
# from matplotlib.patches import Rectangle
# from matplotlib.projections import register_projection
# from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator, FormatStrFormatter


class MyMatplotlibTools:
    def __init__(self):
        pass

    @staticmethod
    def viewport_lim(vector, end_index, start_index=0, corner1=None, corner2=None):
        corner = corner1
        if vector[-1] > (vector[start_index] + 10):
            down_lim = min(vector[:end_index]) - 1
            up_lim = round(max(vector[:end_index]) + 5, -1) + 1  # multiple of 10, just above maximum altitude
        elif vector[-1] < (vector[start_index] - 10):
            down_lim = round(min(vector[:end_index]) - 5, -1) - 1  # multiple of 10, just below minimum altitude
            up_lim = max(vector[:end_index]) + 1
            corner = corner2
        else:
            down_lim = round(min(vector[:end_index]) - 5, -1) - 1  # multiple of 10, just below minimum altitude
            up_lim = round(max(vector[:end_index]) + 5, -1) + 1  # multiple of 10, just above maximum altitude

        if corner is not None:
            return down_lim, up_lim, corner
        else:
            return down_lim, up_lim

    def set_ylimits(self, ax, y, visible_hours):
        ax.set_ylim(self.viewport_lim(y, visible_hours))

    @staticmethod
    def set_grid(ax):
        ax.grid(which='major', axis='x', linewidth=0.75, linestyle='-', color='0.75')
        ax.grid(which='minor', axis='x', linewidth=0.25, linestyle='-', color='0.75')
        ax.grid(which='major', axis='y', linewidth=0.75, linestyle='-', color='0.75')
        ax.grid(which='minor', axis='y', linewidth=0.25, linestyle='-', color='0.75')

    @staticmethod
    def format_date_ticks(ax):
        ax.xaxis.set_major_locator(mdates.HourLocator())
        ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=range(0, 60, 10)))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%#Hh'))
        ax.yaxis.set_major_locator(MultipleLocator(base=5))
        ax.yaxis.set_minor_locator(MultipleLocator(base=1))
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.0f m'))

        sax = ax.secondary_xaxis('top')
        sax.xaxis.set_major_locator(mdates.HourLocator())
        sax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=range(0, 60, 10)))
        sax.xaxis.set_major_formatter(mdates.DateFormatter('%#Hh'))

        return sax

    @staticmethod
    def format_altitude_tick(ax, shift):
        say = ax.secondary_yaxis('right', functions=(lambda a: shift + a,
                                                     lambda a: a - shift))
        say.yaxis.set_major_locator(MultipleLocator(base=5))
        say.yaxis.set_major_formatter(FormatStrFormatter('%.0f m'))

        return say
