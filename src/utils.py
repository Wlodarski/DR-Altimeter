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
