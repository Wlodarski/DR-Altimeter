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

    def best_degree(self):  # TODO: see if it can be improved
        return len(self.x) // 2

    def error_matrix(self):
        """
        cumulative error
        
        :return: [error_up, error_down]
        """
        sum_up = 0
        sum_down = 0
        error_up = []
        error_down = []
        for t in range(0, len(self.x)):
            error = self.y[t] - polyval(self.poly, self.x[t])
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
        return {'time': [dhour2date(ref_hour=ref_hour, dhour=t) for t in self.x],
                'altitude': self.y,
                'error': self.error}

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

        c_fit = {'time': [dhour2date(ref_hour=ref_hour, dhour=t) for t in
                          np.arange(before_first, after_last, one_minute)],
                 'dotted line': [polyval(self.poly, v) for v in
                                 np.arange(before_first, after_last, one_minute)]}
        c_fit['steps'] = list(map(self._int_round, c_fit['dotted line']))
        return c_fit

    def step_changes(self, ref_hour, fix_hour=None):
        times = []
        steps = []
        cfit = self.curvefit_dict(ref_hour=ref_hour)
        previous_step = cfit['steps'][0]
        if fix_hour is not None:
            fix_hour = fix_hour.replace(microsecond=0, second=0)

        for t in cfit['time']:
            i = cfit['time'].index(t)
            current_time = cfit['time'][i]
            current_step = cfit['steps'][i]
            if current_step != previous_step:
                times.append(current_time)
                steps.append(current_step)
            previous_step = current_step
            if current_time == fix_hour:
                times.append(current_time)
                steps.append('fix')  # TODO: translation

        return times, steps
