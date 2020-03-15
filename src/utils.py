from datetime import datetime
from textwrap import fill


def printf(text: str) -> str:
    """
    Print for a 80 characters wide display
    
    :param text: string
    :return: text folded to the right width 
    """
    print(fill(text, 79))
    return text


def nb_date_changes(first_day: datetime, last_day: datetime) -> int:
    """ Number of calendar day changes between the two dates
    
    :param first_day: datetime
    :param last_day: datetime
    :return: number of calendar day changes
    """
    elapsed = last_day.date() - first_day.date()
    return elapsed.days


def nb_days_between(first_day: datetime, last_day: datetime) -> int:
    """
    Number of days (1 day = 24 hours) between two dates
    
    :param first_day: datetime
    :param last_day: datetime
    :return: number of days
    
    """
    elapsed = last_day - first_day
    return elapsed.days


def set_locale_to_user_defaults():
    import locale
    current_locale, encoding = locale.getdefaultlocale()
    locale.setlocale(locale.LC_TIME, current_locale)


def pretty_polyid(polynomial: object, f_text: str = 'f', var_symbol: str = 'x', equal_sign: str = '=') -> str:
    """
    :param polynomial: numpy.ndarray
    :param f_text: function text
    :param var_symbol: variable symbol
    :param equal_sign: equal sign, ex) '>='
    :return: formula on two lines

    Pretty print remplacement for poly1d

    """
    import re
    from numpy import poly1d as ugly

    formula_up, formula_down = re.split('\n', str(ugly(polynomial, variable=var_symbol)), maxsplit=1)
    spaces = ''.rjust(len(f_text + ' ' + equal_sign), ' ')
    return '{s} {u}\n{f} {e} {d}'.format(u=formula_up, d=formula_down, f=f_text, s=spaces, e=equal_sign)
