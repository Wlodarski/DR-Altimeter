import gettext
from datetime import datetime

_ = gettext.gettext

class Forecast:
    def __init__(self):
        self.forecast = []

    def add(self, atm_pressure: float, timestamp=datetime.now(),
            make_chronological: bool = False, allow_overwrite: bool = True) -> bool:

        overwrited = False
        for n in range(len(self.forecast)):
            if self.forecast[n]['date'] == timestamp:
                if allow_overwrite:
                    self.forecast[n]['pressure'] = atm_pressure
                    overwrited = True
                else:
                    raise ValueError(_('Timestamp must be unique. {} already set').format(timestamp))
        if not overwrited:
            self.forecast.append({'date': timestamp, 'pressure': float(atm_pressure)})

        if make_chronological:
            self.reorder_chronologically()

        return overwrited

    def start_date(self, sort_before=True):
        if sort_before:
            _forecast = self.sorted_by('date')
        return _forecast[0]['date']

    def end_date(self, sort_before=True):
        if sort_before:
            _forecast = self.sorted_by('date')
        return _forecast[-1]['date']

    def search(self, key, value):
        return list(filter(lambda f: f[key] == value, self.forecast))

    def get_a_date(self, pressure):
        return self.search('pressure', pressure)[0]['date']

    def get_a_pressure(self, date):
        return self.search('date', date)[0]['pressure']

    def sorted_by(self, key, reverse=False):
        return sorted(self.forecast, key=lambda i: i[key], reverse=reverse)

    def reorder_chronologically(self):
        self.forecast = self.sorted_by('date')


if __name__ == '__main__':
    from time import sleep

    fc = Forecast()
    for hour in range(24):
        fc.add(timestamp=datetime(2020, 2, 5, hour), atm_pressure=990 + hour)
        fc.add(timestamp=datetime(2020, 2, 4, hour), atm_pressure=991 + hour)
        sleep(0.05)

    for data in fc.sorted_by('date'):
        print('{}h {:.2f} hPa'.format(data['date'].strftime('%D %#H'), data['pressure']))

    print(fc.start_date())
