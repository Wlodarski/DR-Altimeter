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

import warnings
from datetime import datetime, timedelta

import numpy as np
from numpy import polyval, polyfit


def dhour2date(ref_hour: datetime, dhour: float) -> datetime:
    """
    converts decimal hours back to datetime
    
    :param ref_hour: reference datetime from which decimal hour = 0.0  
    :param dhour: 
    :return: 
    """
    return ref_hour + timedelta(hours=dhour)


def date2dhour(date_ref: datetime, date: datetime) -> float:
    """
    converts date to decimal hour format
    
    :param date_ref: origin, sets when decimal hour = 0.0
    :param date: 
    :return: 
    """
    return (date - date_ref).total_seconds() / 3600


class PolynomialCurveFit:
    def __init__(self, x_vector, y_vector):
        self.x = x_vector
        self.y = y_vector
        self.degree = self.best_degree()
        self.poly = polyfit(self.x, self.y, self.degree)
        self.error = self.error_matrix()

    # def best_degree(self):
    #     return len(self.x) // 2

    def best_degree(self) -> int:
        """
        Finds the polynomial degree with the best fit by removing one point of data
        :return: degree with least square error
        """
        error_for_each_degree = []
        full_len = len(self.x)
        half_len = full_len // 2
        slightly_larger_than_half = (4 * full_len) // 7  # 4/7 is slightly larger than 1/2
        for tested_degree in range(slightly_larger_than_half):
            squared_error = 0
            for index_removed in range(full_len):
                training_x = self.x.copy()
                training_y = self.y.copy()
                del training_x[index_removed]
                del training_y[index_removed]
                # RankWarning should never be triggered with a 4/7 ceiling
                # Hence the warning is not currently supressed
                #
                # code to supress warning, for future reference:
                #       warnings.simplefilter('ignore', np.RankWarning)
                #
                poly = polyfit(training_x, training_y, tested_degree)
                squared_error += (self.y[index_removed] - polyval(poly, self.x[index_removed])) ** 2
            error_for_each_degree.append(np.sqrt(squared_error))
        best = np.argmin(error_for_each_degree)
        if best >= half_len:
            warnings.warn(_("Degree abnormally high. Predictions might be unreliable."))
        return best

    def error_matrix(self):
        """
        cumulative error
        
        :return: [error_up, error_down]
        """
        sum_up = 0
        sum_down = 0
        error_up = []
        error_down = []
        for time, altitude in zip(self.x, self.y):
            curve_fit_altitude = polyval(self.poly, time)
            error = altitude - curve_fit_altitude
            if error > 0:
                sum_up += error
            else:
                sum_down -= error
            error_up.append(sum_up)
            error_down.append(sum_down)
        return error_up, error_down

    def prediction_dict(self, ref_hour):
        """
        :param ref_hour: 
        |:return:  {'time': [x],
        |           'altitude': [y],
        |           'error': [(error_up, error_down)]}
        """
        return {
            "time": [dhour2date(ref_hour=ref_hour, dhour=t) for t in self.x],
            "altitude": self.y,
            "error": self.error,
        }

    @staticmethod
    def _int_round(x):
        return int(round(x))

    def curvefit_dict(self, ref_hour, margin=None):
        first = self.x[0]
        last = self.x[-1]
        one_minute = 1 / 60

        if margin is None:  # minutes to reach full_hour

            before_first = 0
            after_last = last

        else:  # symetrical margin

            before_first = first - margin * one_minute
            after_last = last + margin * one_minute

        c_fit = {
            "time": [dhour2date(ref_hour=ref_hour, dhour=t) for t in np.arange(before_first, after_last, one_minute)],
            "dotted line": [polyval(self.poly, v) for v in np.arange(before_first, after_last, one_minute)],
        }
        c_fit["steps"] = list(map(self._int_round, c_fit["dotted line"]))
        return c_fit

    def step_changes(self, ref_hour, fix_hour=None):
        times = []
        steps = []
        cfit = self.curvefit_dict(ref_hour=ref_hour)
        previous_step = cfit["steps"][0]
        if fix_hour is not None:
            fix_hour = fix_hour.replace(microsecond=0, second=0)

        for current_time, current_step in zip(cfit["time"], cfit["steps"]):
            if current_step != previous_step:
                times.append(current_time)
                steps.append(current_step)
            previous_step = current_step
            if current_time == fix_hour:
                times.append(current_time)
                steps.append(_("fix"))

        return times, steps
