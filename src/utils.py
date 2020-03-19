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
    """ 
    Number of calendar day changes between the two dates
    
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


def pretty_polyid(polynomial: object, f_text: str = "f", var_symbol: str = "x", equal_sign: str = "=") -> str:
    """
    Pretty print remplacement for poly1d
    
    
    :param polynomial: numpy.ndarray
    :param f_text: function text
    :param var_symbol: variable symbol
    :param equal_sign: equal sign, ex) '>='
    :return: formula on two lines


    """
    import re
    from numpy import poly1d as ugly

    formula_up, formula_down = re.split("\n", str(ugly(polynomial, variable=var_symbol)), maxsplit=1)
    spaces = "".rjust(len(f_text + " " + equal_sign), " ")
    return f"{spaces} {formula_up}\n{f_text} {equal_sign} {formula_down}"


def cross_platform_leading_zeros_removal(s, c="#"):
    """
    
    | Removes leading zeros. For instance, #05h12 becomes 5h12. 
    |
    | Required because strftime %#H (Windows) and %-H (Linux) are platform dependant 
    |
       
    :param s: string
    :param c: character that signals possible leading zeros 
    :return: string without any leading zeros
    
    
    """
    return s.replace(c + "0", c).replace(c, "")
