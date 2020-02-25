import gettext

_ = gettext.gettext


class InternationalStandardAtmosphere:
    """
     | Assumptions:
     |
     |   a) altitude below 11 km
     |   b) barometric altimeter at constant temperature and humidity
    """

    def __init__(self):

        self.TEMP_MSL = 288.15  # Kelvin; Temperature at Mean Sea Level
        self.PRESSURE_MSL = 1013.25  # hPa; Pressure at Mean Sea Level
        self.TEMP_GRADIANT = 6.5 / 1000  # Kelvin per meter; Rate at which temperature decreases with altitude
        self.PERFECT_GAS = 5.255  # dimensionless; Viscosity and compressibility of dry air, behaving like a perfect gas

    def pressure(self, altitude: float) -> float:
        """    
        :param altitude: altitude in meters
        :return: pressure (in hPa) found at this altitude 

        Pressure found at an altitude above Mean Sea Level 
        according to the International Standard Atmosphere (ISA) model
        """
        if -700 < altitude < 10000:
            return self.PRESSURE_MSL * (1 - (altitude / (self.TEMP_MSL / self.TEMP_GRADIANT))) ** self.PERFECT_GAS
        else:
            raise ValueError(_('Altitude out of range (-700 m < altitude < 10000 m)'))

    def altitude(self, pressure: float) -> float:
        """
        :param pressure: pressure in hPa 
        :return: altitude (in meters) corresponding to this pressure

        Altitude above Mean Sea Level whilst experiencing this pressure
        according to the International Standard Atmosphere (ISA) model
        """
        if 260 < pressure < 1100:
            return (self.TEMP_MSL / self.TEMP_GRADIANT) * (1 - (pressure / self.PRESSURE_MSL) ** (1 / self.PERFECT_GAS))
        else:
            raise ValueError(_('Pressure out of range (260 hPa < pressure < 1100 hPa)'))

    def delta_altitude(self, p_ref: float, current_p: float = None, delta_p: float = None) -> float:
        """
        :param p_ref: reference pressure in hPa
        :param current_p: current pressure in hPa
        :param delta_p: how much (in hPa) the pressure departed from the reference pressure
        :return: equivalent climb/descent in meters

        How much meters one climbed or descended when starting at a reference pressure
        according to the International Standard Atmosphere (ISA) model.
        
        Either the current pressure or the pressure variation needs to be provided,
        not both.
        """
        if current_p is None and delta_p is None:
            raise ValueError(_('Missing current pressure or pressure variation'))

        if current_p is not None:
            _dp = p_ref - current_p
            _cp = current_p

        if current_p is not None and delta_p is not None and _dp != delta_p:
            raise ValueError(_('Current pressure contradicted by pressure variation'))

        if delta_p is not None:
            _cp = p_ref + delta_p

        return self.altitude(pressure=_cp) - self.altitude(pressure=p_ref)

    def correction(self, p_start: float = 1013.25, p_end: float = None, delta_p: float = None) -> float:
        """
        :param p_start: starting pressure in hPa, defaults to mean sea level pressure
        :param p_end: ending pressure in hPa
        :param delta_p: pressure variation in hPa
        :return: correction to apply in meters


        How much a barometric altimeter not moving needs to be corrected to display a constant altitude
        after experiencing a change in atmospheric pressure due to weather
        """
        return -self.delta_altitude(p_ref=p_start, current_p=p_end, delta_p=delta_p)


if __name__ == '__main__':
    isa = InternationalStandardAtmosphere()

    alt = 1200
    print(_('At {} m above mean sea level, '
            'the standardized atmospheric pressure equals {:.2f} hPa').format(alt, isa.pressure(altitude=alt)))

    pres = 800.0
    print(_('A pressure of {:.2f} hPa corresponds '
            'to a standardized altitude of {:.0f} m').format(pres, isa.altitude(pressure=pres)))

    print()
    print(_('Average Correction').center(73))
    print('+/-hPa |', end='')
    for d in range(0, 11):
        print('{:5.1f}'.format(d / 10), end=' ')
    print()
    print('-------+' + ''.center(65, '-'))
    for alt in [-500, 0, 500, 1000, 2000, 3000, 4000, 5000]:
        pref = isa.pressure(altitude=alt)
        print('{:4}'.format(alt), end=' m |')
        for d in range(0, 11):
            pressure_variation = d / 10
            plus = isa.correction(p_start=pref, delta_p=pressure_variation)
            minus = isa.correction(p_start=pref, delta_p=-pressure_variation)
            average = (plus - minus) / 2
            print('{:5.2f}'.format(average), end=' ')
        print()