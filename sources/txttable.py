class PredictionTable:
    def __init__(self):
        from texttable import Texttable

        self.table = Texttable()
        self.table.set_deco(Texttable.HEADER | Texttable.HLINES)
        self.table.set_cols_dtype(['t', 't', 't', 't', 't'])
        self.table.set_cols_align(['c', 'r', 'r', 'r', 'l'])
        self.table.set_cols_valign(['t', 't', 't', 't', 'm'])
        self.table.header(['H', 'PRESSURE', 'ALT', 'ALT/hr', ''])
        self.table.set_cols_width([5, 11, 7, 6, 38])  # total width = 80 (with added borders)

    def _add(self, hour: str, pressure: str, alt: str = '', alt_h: str = '', times: str = ''):
        return self.table.add_row([hour, pressure, alt, alt_h, times])

    def add_start(self, hour: int, minute: int, pressure: float, times: iter):
        _h = '{:d}h{:02d}'.format(int(hour), int(minute))
        _p = '{:.2f} hPa'.format(float(pressure))
        _t = ', '.join(times)

        return self._add(hour=_h, pressure=_p, times=_t)

    def add(self, hour: int, pressure: float, alt: float, alt_h: float, times: iter) -> int:
        _h = '{:d}h'.format(int(hour))
        _p = '{:.2f} hPa'.format(float(pressure))
        _a = '{:.1f}m'.format(float(alt))
        _ah = '{:.1f}m'.format(float(alt_h))
        # _c = '{:d}'.format(int(round(cor)))
        _t = ', '.join(times)

        return self._add(hour=_h, pressure=_p, alt=_a, alt_h=_ah, times=_t)

    def display_table(self):
        return self.table.draw()


if __name__ == '__main__':
    tt = PredictionTable()
    tt.add_start(hour=9, minute=12, pressure=1017.61, times=['9h00', '9h08~9h12 fix', '9h28', '9h42'])
    tt.add(hour=10, pressure=1017.101, alt=4.2, alt_h=4.2,
           times=['10h09', '10h18', '10h27', '10h36', '10h45', '10h54', '10h59'])
    tt.add(hour=11, pressure=1016.3, alt=10.89999, alt_h=6.6,
           times=['11h03', '11h05', '11h10', '11h15', '11h21', '11h26', '11h31',
                  '11h36', '11h41', '11h46', '11h52', '11h57'])
    print(tt.display_table())
