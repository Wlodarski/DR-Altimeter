#! python3

# https://stackoverflow.com/questions/56701417/how-to-suppress-all-warnings-in-window-of-executable-file-generated-by-pyinstall
# https://chromedriver.storage.googleapis.com/index.html
# https://icoconvert.com/
# https://github.com/matplotlib/matplotlib/issues/15621

import argparse
import logging
import traceback
from abc import abstractmethod
from configparser import ConfigParser
from datetime import datetime, timedelta
from os import system, environ
from pathlib import Path
from re import search
from textwrap import fill
from time import strftime

import colorama
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import slack
from matplotlib.axes import Axes
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle
from matplotlib.projections import register_projection
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from termcolor import colored

from ISA import InternationalStandardAtmosphere
from forecastarray import Forecast
from txttable import PredictionTable

colorama.init()  # otherwise termcolor won't be fully included at compilation by pyinstaller

FULLNAME = 'DR Polynomial Altimeter'
VERSION = '0.9.20 alpha'
DESCRIPTION = "Altitude 'Dead Reckoning' for Casio Triple Sensor v.3"
SHORTNAME = 'DR-Altimeter'

parser = argparse.ArgumentParser(Path(__file__).name,
                                 description=DESCRIPTION,
                                 epilog='{}, version {}'.format(SHORTNAME, VERSION))
parser.add_argument('-n', '--no-key', action='store_true', help='Disable "Press any key"')
parser.add_argument('-s', '--slack', help='Slack channel')
parser.add_argument('--latitude', help='Latitude', type=float)
parser.add_argument('--longitude', help='Longitude', type=float)
parser.add_argument('--override-url', help='Specific weather station URL', type=str)
parser.add_argument('-v', '--verbose', action='store_true')

args = parser.parse_args()

if (args.longitude is not None and args.latitude is None) or (args.longitude is None and args.latitude is not None):
    parser.error('If one is provided, both --latitude and --longitude must be provided')


class Program:
    def __init__(self, fullname: str, version: str, description: str, shortname: str):
        """
        :param fullname: program name
        :param version: program version
        :param description: short description
        :param shortname: short name, mainly for logs
        """

        global args

        self.NAME = fullname
        self.SHORTNAME = shortname
        self.VERSION = version
        self.DESCRIPTION = description

        self.STATION_NAME = None
        self.ELEVATION = None
        self.P_INITIAL = None

        self.console = Console(title=self.NAME, version=self.VERSION, subtitle=self.DESCRIPTION)
        self.result = PredictionTable()
        self.forecast = Forecast()
        self.slack = slack.WebClient(token=environ['SLACK_API_TOKEN'])

        # starts logging
        self.LOG_FILENAME = self.SHORTNAME + '.log'
        logging.basicConfig(filename=self.LOG_FILENAME,
                            level=logging.INFO,
                            filemode='w',
                            format="%(asctime)s %(levelname)s : %(message)s",
                            datefmt='%Y-%m-%d %H:%M'
                            )

        # reads configuration file and recreates missing values
        self.CONFIG_FILENAME = 'config.ini'
        self.CS = 'USER SETTINGS'
        self.cfg = ConfigParser()
        self.cfg.read(self.CONFIG_FILENAME)

        if self.CS not in self.cfg.sections():
            print('Regenerating ', self.CONFIG_FILENAME)
            print()
            self.cfg.add_section(self.CS)

        self.TIMEOUT_T = 'short timeout'
        self.TIMEOUT = int(self.cfg.get(self.CS, self.TIMEOUT_T, fallback='5'))

        self.TIMEOUT_LONG_T = 'long timeout'
        self.TIMEOUT_LONG = int(self.cfg.get(self.CS, self.TIMEOUT_LONG_T, fallback='10'))

        self.GEOLOCATION_ALWAYS_ON_T = 'geolocation always on'
        self.GEOLOCATION_ALWAYS_ON = bool(int(self.cfg.get(self.CS, self.GEOLOCATION_ALWAYS_ON_T, fallback='0')))

        self.WAIT_FOR_KEY_T = 'press any key'
        self.WAIT_FOR_KEY = bool(int(self.cfg.get(self.CS, self.WAIT_FOR_KEY_T, fallback='1')))
        self.PAUSE = (not args.no_key) and self.WAIT_FOR_KEY

        self.OVERRIDE_URL_T = 'override url'
        self.OVERRIDE_URL_ = self.cfg.get(self.CS, self.OVERRIDE_URL_T, fallback='')
        if args.override_url is not None:
            self.OVERRIDE_URL = args.override_url
        else:
            self.OVERRIDE_URL = self.OVERRIDE_URL_

        self.OVERRIDE_URL_EXISTS = self.OVERRIDE_URL is not None and len(self.OVERRIDE_URL) > 35

        self.ANY_HTTPS_PAGE_T = 'https page'
        self.ANY_HTTPS_PAGE = self.cfg.get(self.CS, self.ANY_HTTPS_PAGE_T, fallback='https://blank.org')

        self.GEOLOCATED_URL_T = 'wunderground hourly url'
        self.GEOLOCATED_URL = self.cfg.get(self.CS, self.GEOLOCATED_URL_T,
                                           fallback='https://www.wunderground.com/hourly/ca/location/')

        self.GRAPH_FILENAME_T = 'autosave png-pdf-eps filename'
        self.GRAPH_FILENAME = self.cfg.get(self.CS, self.GRAPH_FILENAME_T, fallback='graph.png')

        self.GRAPH_DPI_T = 'autosave dpi'
        self.GRAPH_DPI = int(self.cfg.get(self.CS, self.GRAPH_DPI_T, fallback='600'))

        self.GRAPH_ORIENTATION_T = 'autosave orientation'
        self.GRAPH_ORIENTATION = self.cfg.get(self.CS, self.GRAPH_ORIENTATION_T, fallback='landscape')

        self.GRAPH_PAPERTYPE_T = 'autosave papertype'
        self.GRAPH_PAPERTYPE = self.cfg.get(self.CS, self.GRAPH_PAPERTYPE_T, fallback='letter')

        self.VERBOSE_T = 'verbose'
        self.VERBOSE_ = bool(int(self.cfg.get(self.CS, self.VERBOSE_T, fallback='0')))
        self.VERBOSE = self.VERBOSE_ or args.verbose

        self.SHOW_X_HOURS_T = 'display x hours'
        self.SHOW_X_HOURS = max(int(self.cfg.get(self.CS, self.SHOW_X_HOURS_T, fallback='6')), 1)

        self.MIN_HOURS_T = 'minimum hours'
        self.MIN_HOURS = max(int(self.cfg.get(self.CS, self.MIN_HOURS_T, fallback='8')), self.SHOW_X_HOURS)

        self.save_ini()  # save immediately to renew all required values

        # optional values that can be missing
        self.LATITUDE_T = 'latitude'
        self.LONGITUDE_T = 'longitude'
        self.LATITUDE = None
        self.LONGITUDE = None

        if args.latitude is not None:
            self.LATITUDE = args.latitude
        elif self.cfg.has_option(self.CS, self.LATITUDE_T):
            self.LATITUDE = float(self.cfg.get(self.CS, self.LATITUDE_T))

        if args.longitude is not None:
            self.LONGITUDE = args.longitude
        elif self.cfg.has_option(self.CS, self.LONGITUDE_T):
            self.LONGITUDE = float(self.cfg.get(self.CS, self.LONGITUDE_T))

        self.MISSING_LATLONG = self.LATITUDE is None or self.LONGITUDE is None

        self.browser = ChromeBrowser()

    def save_ini(self):
        self.cfg.set(self.CS, self.VERBOSE_T, str(int(self.VERBOSE_)))
        self.cfg.set(self.CS, self.TIMEOUT_T, str(self.TIMEOUT))
        self.cfg.set(self.CS, self.TIMEOUT_LONG_T, str(self.TIMEOUT_LONG))
        self.cfg.set(self.CS, self.SHOW_X_HOURS_T, str(self.SHOW_X_HOURS))
        self.cfg.set(self.CS, self.MIN_HOURS_T, str(self.MIN_HOURS))
        self.cfg.set(self.CS, self.ANY_HTTPS_PAGE_T, self.ANY_HTTPS_PAGE)
        self.cfg.set(self.CS, self.GEOLOCATED_URL_T, self.GEOLOCATED_URL)
        self.cfg.set(self.CS, self.GEOLOCATION_ALWAYS_ON_T, str(int(self.GEOLOCATION_ALWAYS_ON)))
        self.cfg.set(self.CS, self.OVERRIDE_URL_T, str(self.OVERRIDE_URL_))
        self.cfg.set(self.CS, self.WAIT_FOR_KEY_T, str(int(self.WAIT_FOR_KEY)))
        self.cfg.set(self.CS, self.GRAPH_FILENAME_T, self.GRAPH_FILENAME)
        self.cfg.set(self.CS, self.GRAPH_DPI_T, str(self.GRAPH_DPI))
        self.cfg.set(self.CS, self.GRAPH_ORIENTATION_T, self.GRAPH_ORIENTATION)
        self.cfg.set(self.CS, self.GRAPH_PAPERTYPE_T, self.GRAPH_PAPERTYPE)

        with open(self.CONFIG_FILENAME, 'w') as configfile:
            self.cfg.write(configfile)

    def save_lat_lon(self, pos):
        self.cfg.set(self.CS, self.LATITUDE_T, str(pos['latitude']))
        self.cfg.set(self.CS, self.LONGITUDE_T, str(pos['longitude']))
        self.save_ini()

        print('Latitude : {:.7f}'.format(pos['latitude']))
        print('Longitude : {:.7f}'.format(pos['longitude']))
        print('Accuracy : {}m'.format(pos['accuracy']))
        logging.info('{:.7f} {:.7f} ±{}m'.format(pos['latitude'], pos['longitude'], pos['accuracy']))
        print()

    def hourly_forecast_url(self):
        if self.GEOLOCATION_ALWAYS_ON or (self.MISSING_LATLONG and not self.OVERRIDE_URL_EXISTS):

            self.browser.go_to(webpage=self.ANY_HTTPS_PAGE, geolocation=True)
            position = self.browser.get_lat_lon()
            self.save_lat_lon(pos=position)
            self.browser.quit()

            #  decreased precision (4 digits instead of 7) to partially preserve anonymity
            _hourly_forecast_url = self.GEOLOCATED_URL + '{:.4f},{:.4f}'.format(position['latitude'],
                                                                                position['longitude'])

        elif self.OVERRIDE_URL_EXISTS:

            print('Using override URL')
            _hourly_forecast_url = self.OVERRIDE_URL

        elif not self.MISSING_LATLONG:

            if args.latitude is None:
                print('Using Lat/Lon found in', self.CONFIG_FILENAME)
            print('Latitude: {}'.format(self.LATITUDE))
            print('Longitude: {}'.format(self.LONGITUDE))
            print()
            _hourly_forecast_url = self.GEOLOCATED_URL + '{},{}'.format(
                self.LATITUDE,
                self.LONGITUDE)

        else:  # if everything fails, an example url
            _hourly_forecast_url = 'https://www.wunderground.com/hourly/ca/montreal/IMONTR15'

        return _hourly_forecast_url

    def check_page(self, title: str):
        """ Make sure we are on the right page by checking the title"""
        try:
            assert title in self.browser.driver.title
        except AssertionError:
            raise NameError('Page with wrong title')

        print('Connected to Wunderground')

    def wait_until_page_is_loaded(self):
        try:
            WebDriverWait(self.browser.driver, self.TIMEOUT).until(
                ec.presence_of_element_located((By.ID, 'hourly-forecast-table')))
            print('Page is ready')
        except TimeoutException:
            raise TimeoutException('Page took too much time to load')

    def switch_to_metric(self):
        print('Switching to metric')
        self.browser.driver.find_element_by_id('wuSettings').click()
        self.browser.driver.find_element_by_css_selector("[title^='Switch to Metric'").click()
        try:
            WebDriverWait(self.browser.driver, self.TIMEOUT_LONG).until(
                ec.text_to_be_present_in_element((By.ID, 'hourly-forecast-table'), 'hPa'))
        except TimeoutException:
            raise TimeoutException('Unable to switch to metric')

    def click_next(self):
        self.browser.driver.find_element_by_xpath('//*[@id="nextForecasts"]/span[2]/button').click()

    def get_station_name(self):
        try:
            _elem = self.browser.driver.find_element_by_xpath(
                '//*[@id="inner-content"]/div[2]/lib-city-header/div[1]/div/div/a[1]')
            _st = search('^-?[0-9]* (.*)$', _elem.text)
            self.STATION_NAME = _st.group(1).strip()
        except NoSuchElementException:
            print(self.register_error('Station name not found'))
        if self.STATION_NAME is None or self.STATION_NAME == 'STATION':
            try:
                _elem = self.browser.driver.find_element_by_xpath(
                    '//*[@id="inner-content"]/div[2]/lib-city-header/div[1]/div/h1')
                self.STATION_NAME = _elem.text[:20].lstrip(', ') + '...'
            except NoSuchElementException:
                self.STATION_NAME = 'UNKNOWN'
        logging.info(self.STATION_NAME)
        print()
        print(colored(self.STATION_NAME, attrs=['bold']))

    def get_atm_pressure_at_station(self):
        _elem = self.browser.driver.find_element_by_xpath('//*[@id="inner-content"]/div[3]/div[2]/div/div[1]'
                                                          '/div[1]/lib-additional-conditions/lib-item-box/div/'
                                                          'div[2]/div/div[1]/div[2]/lib-display-unit/span/span[1]')
        self.P_INITIAL = float(_elem.text)
        print(self.register_info('Current atmospheric pressure : '
                                 '{} hPa (ISA={:0.1f}m)'.format(self.P_INITIAL, isa.altitude(pressure=self.P_INITIAL))))
        return self.P_INITIAL

    def get_obs_time(self):
        _elem = self.browser.driver.find_element(By.XPATH, '//*[@id="app-root-state"]')
        _st = search('obsTimeLocal&q;:&q;(....-..-.. ..:..:..)&q;', _elem.get_attribute('innerHTML'))
        if _st is not None:
            return datetime.strptime(_st.group(1), '%Y-%m-%d %H:%M:%S')
        else:
            print(self.register_error('Observation time not found.'))
            return datetime.now()

    def get_station_elevation(self):
        try:
            _elem = self.browser.driver.find_element(By.XPATH, '//*[@id="inner-content"]/div[2]'
                                                               '/lib-city-header/div[1]/div/span/span/strong')
            self.ELEVATION = int(_elem.text)
        except NoSuchElementException:
            print(self.register_error('Elevation not found. Assuming it to be zero'))
            self.ELEVATION = 0
        print(self.register_info('Weather station elevation : '
                                 '{}m (ISA={:7.2f}hPa)'.format(self.ELEVATION, isa.pressure(altitude=self.ELEVATION))))

    def display_results(self):
        _txt = self.result.display_table()
        logging.info('\n\n' + _txt)
        print(_txt)
        if args.slack is not None:
            _title = '{}-{}.txt'.format(self.STATION_NAME, strftime('%Y%m%d-%H%M')).replace(' ', '_')
            _comment = '{st} ({el}m)\n\n'.format(st=self.STATION_NAME, el=self.ELEVATION)
            try:
                _response = self.slack.files_upload(content=_txt,
                                                    channels=args.slack,
                                                    title=_title,
                                                    initial_comment=_comment)
                assert _response["ok"]
            except AssertionError:
                print(self.register_error('Unable to send report to Slack'))

    @staticmethod
    def register_info(msg):
        logging.info(msg=msg)
        return msg

    @staticmethod
    def register_error(msg):
        logging.error(msg)
        return msg


class Console:
    def __init__(self, title: str, version: str, subtitle: str):
        """
        :param title: window title
        :param version: program version
        :param subtitle: short description
        """
        self.title = title
        self.version = version
        self.subtitle = subtitle

        system('title {name} {version}'.format(name=self.title, version=self.version))

        print(colored('{name} {version}'.format(name=self.title, version=self.version), attrs=['bold']))
        print(self.subtitle)
        print()


class ChromeBrowser:
    """ Controls *chromedriver.exe* """

    def __init__(self):
        self.options = Options()
        self._listening_on_disabled()
        self.driver = None

    def _listening_on_disabled(self):
        self.options.add_argument('--log-level=3')
        self.options.add_experimental_option('excludeSwitches', ['enable-logging'])

    def go_to(self, webpage: str, hidden: bool = False, geolocation: bool = False):
        """ Open browser """
        self.options.add_experimental_option('prefs', {'geolocation': geolocation})
        if hidden and not geolocation:  # geolocation only works if not headless
            self.options.add_argument('--headless')
        self.driver = webdriver.Chrome(chrome_options=self.options)
        self.driver.get(webpage)

    def close_window(self):
        """ Close the browser window that the driver has focus of """
        self.driver.close()

    def quit(self):
        """ Close all remaining browsers and safely ends the session """
        self.driver.quit()

    def get_lat_lon(self):
        # Since getCurrentPosition is an asynchroneous Javascript function
        # Python waits until done() is called with the results passed as parameters
        _position = self.driver.execute_async_script(
            "var done = arguments[0]; "
            "navigator.geolocation.getCurrentPosition(function (pos){done(pos.coords);});"
        )
        self.close_window()

        return _position


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


class NoPanXAxes(Axes):
    """Defintion of a Matplotlib Projection that forbids any perpendiculat (up/down) pan"""
    name = 'No Pan X Axes'

    @abstractmethod
    def drag_pan(self, button, key, _x, _y):
        Axes.drag_pan(self, button, 'x', _x, _y)  # pretend key=='x'


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


# =====================================================================
#  MAIN
# =====================================================================

program = Program(fullname=FULLNAME, version=VERSION, description=DESCRIPTION, shortname=SHORTNAME)
isa = InternationalStandardAtmosphere()

# noinspection PyBroadException
try:
    hourly_forecast_url = program.hourly_forecast_url()

    one_hour = timedelta(hours=1)
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=program.MIN_HOURS)

    dates = []
    hours = []
    date = start_time + one_hour
    while date <= end_time:
        this_day = date.strftime('%Y-%m-%d')
        hours.append(date.strftime('%H'))
        if this_day not in dates:
            dates.append(this_day)
        date += one_hour

    first = True
    for d in dates:
        if program.VERBOSE:
            print(hourly_forecast_url + '/date/' + d)
        if first:
            program.browser.go_to(webpage=hourly_forecast_url + '/date/' + d, hidden=True)
            program.check_page(title='Hourly Weather Forecast | Weather Underground')
            program.wait_until_page_is_loaded()
            program.switch_to_metric()
            first = False
        else:
            program.click_next()

        if program.STATION_NAME is None:
            program.get_station_name()
        if program.ELEVATION is None:
            program.get_station_elevation()
        if program.P_INITIAL is None:
            program.forecast.add(atm_pressure=program.get_atm_pressure_at_station(), timestamp=program.get_obs_time())
            print()

        elem = program.browser.driver.find_element(By.ID, 'hourly-forecast-table')
        for row in elem.text.split('\n'):
            if not row.startswith('Time'):  # skips the header row, which starts with the word Time

                # parsing out hour and predicted pressure
                st = search('^([0-9]+:00 [ap]m).* (.*) hPa$', row)
                hour = datetime.strptime(d + ' ' + st.group(1), '%Y-%m-%d %I:%M %p')
                pressure = float(st.group(2).replace(',', ''))
                program.forecast.add(atm_pressure=pressure, timestamp=hour)

    program.browser.quit()

    start = program.forecast.forecast[0]['date']
    end = program.forecast.forecast[-1]['date']

    starting_full_hour = start.replace(microsecond=0, second=0, minute=0)
    ending_full_hour = end.replace(microsecond=0, second=0, minute=0)

    x = []  # delta time
    x_labels = []  # labels for graph
    y = []  # delta alt
    z = []  # forecasted pressure

    for data in program.forecast.sorted_by('date'):
        difference = data['date'] - starting_full_hour
        decimal_elapse_hours = difference.total_seconds() / 3600
        x.append(decimal_elapse_hours)
        x_labels.append(data['date'].strftime('%#Hh'))
        y.append(isa.delta_altitude(p_ref=program.P_INITIAL, current_p=data['pressure']))
        z.append(data['pressure'])

    # ----------------------------------------------------------------------
    # POLYNOMIAL CURVE FIT
    # ----------------------------------------------------------------------

    if program.VERBOSE:
        print(program.register_info(' POLYNOMIAL CURVE FIT '.center(79, '=')))
        print()

    # seeks to find a degree that fits the fix  # TODO: optimize fix + later
    pass_through_zero = 0
    half_point = len(x) // 2
    for d in range(1, half_point + 1):
        p = np.polyfit(x, y, d)
        test = round(np.polyval(p, int(datetime.now().strftime('%M')) / 60))
        if test == 0:
            pass_through_zero += 1
        else:
            if pass_through_zero > 0:
                pass_through_zero += -1
        if program.VERBOSE:
            print(program.register_info('Degree : {:2d}/{}, '
                                        'passing through zero {} times'.format(d, half_point, pass_through_zero)))
        if pass_through_zero == 2:  # TODO
            if program.VERBOSE:
                print('Found a good match')
                print()
            break
    else:
        if program.VERBOSE:
            # d += 1
            print(program.register_info('End of search'))
            print()
    degree = d  # - 1
    poly = np.polyfit(x, y, degree)

    if program.VERBOSE:
        print(program.register_info('Degree : {}'.format(degree)))
        print()
        print(fill(program.register_info('Coefficients : {}'.format(poly)), 79))
        print()
        print(fill(program.register_info('Time vector (x) : {}'.format(x)), 79))
        print()
        print(fill(program.register_info('Altitude vector (y) : {}'.format(y)), 79))
        print()
        print(fill(program.register_info('Pressure vector (z) : {}'.format(z)), 79))
        print()
        print(program.register_info('\n{}\n'.format(pretty_polyid(polynomial=poly,
                                                                  f_text='altitude(time)',
                                                                  var_symbol='time',
                                                                  equal_sign='='))))
        print(program.register_info(''.center(79, '-')))
        print()

    lower_err = []
    upper_err = []
    total_up_err = 0
    total_down_err = 0
    previous_v = None
    fix_found = False
    now_minutes = int(datetime.now().strftime('%M'))
    for t in range(0, len(x)):
        steps = []
        for minutes in range(0, 60):
            minute_dec = minutes / 60
            t_dec = t + minute_dec
            v = round(np.polyval(poly, t_dec))

            if not fix_found and minutes == now_minutes:
                fix_found = True
                steps.append('{}[fix]'.format(datetime.now().strftime('%Hh%M')))

            if previous_v is None:
                previous_v = v

            if v != previous_v:
                change_time = program.forecast.forecast[t]['date'].replace(microsecond=0,
                                                                           second=0,
                                                                           minute=minutes)
                steps.append('{}[{:d}]'.format(change_time.strftime('%Hh%M'), int(v)))
                previous_v = v

        if t == 0:
            old = 0
            program.result.add_start(hour=start.strftime('%H'),
                                     minute=start.strftime('%M'),
                                     pressure=program.P_INITIAL,
                                     times=steps)
        else:
            program.result.add(hour=program.forecast.forecast[t]['date'].strftime('%#H'),
                               pressure=program.forecast.forecast[t]['pressure'],
                               alt=y[t],
                               alt_h=y[t] - old,
                               times=steps)
            old = y[t]

        err = np.polyval(poly, x[t]) - y[t]
        if err > 0:
            total_up_err += err
        else:
            total_down_err += -err

        lower_err.append(total_down_err)
        upper_err.append(total_up_err)

    program.display_results()

    # --------------------------------------------------------------------------
    # GRAPH
    # --------------------------------------------------------------------------

    register_projection(NoPanXAxes)

    nb_hours = min(program.SHOW_X_HOURS + 1, len(x))

    # one figure
    fig = plt.figure(dpi=96, figsize=(16, 9), num='{} {}'.format(program.STATION_NAME, strftime('%Y%m%d-%H%M')))
    plt.figtext(0.95, 0.01,
                '{} {}'.format(program.NAME, program.VERSION), horizontalalignment='right',
                alpha=0.8, fontsize='x-small')

    # two subplots on a grid system
    gs = GridSpec(figure=fig, ncols=1, nrows=2, height_ratios=[3, 1], hspace=0.1, bottom=0.07)
    topsubplot = fig.add_subplot(gs[0], title='{} ― {}'.format(program.STATION_NAME, strftime('%Y.%m.%d %H:%M')))
    bottomsubplot = fig.add_subplot(gs[1], sharex=topsubplot, projection='No Pan X Axes')

    # formatting the top (altitude) graph
    topsubplot.set_xlim(x[0] - 10 / 60, nb_hours)
    loc = 'lower right'
    if y[-1] > (y[0] + 10):
        down_lim = min(y[:nb_hours]) - 1
        up_lim = round(max(y[:nb_hours]) + 5, -1) + 1  # multiple of 10, just above maximum altitude
    elif y[-1] < (y[0] - 10):
        down_lim = round(min(y[:nb_hours]) - 5, -1) - 1  # multiple of 10, just below minimum altitude
        up_lim = max(y[:nb_hours]) + 1
        'upper right'
    else:
        down_lim = round(min(y[:nb_hours]) - 5, -1) - 1  # multiple of 10, just below minimum altitude
        up_lim = round(max(y[:nb_hours]) + 5, -1) + 1  # multiple of 10, just above maximum altitude
    topsubplot.set_ylim(down_lim, up_lim)
    topsubplot.set_ylabel('$\Delta$altitude, $m$')
    topsubplot.xaxis.set_major_formatter(ticker.IndexFormatter(x_labels))
    topsubplot.xaxis.set_major_locator(ticker.MultipleLocator(base=1))
    topsubplot.xaxis.set_minor_locator(ticker.AutoMinorLocator(n=6))
    topsubplot.yaxis.set_major_locator(ticker.MultipleLocator(base=5))
    topsubplot.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f m'))
    topsubplot.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=5))
    topsubplot.grid(True, which='major', alpha=0.6)
    topsubplot.grid(True, which='minor', alpha=0.3)

    top_second_y_axis = topsubplot.secondary_yaxis("right",
                                                   functions=(lambda b: program.ELEVATION + b,
                                                              lambda b: b - program.ELEVATION))
    top_second_y_axis.set_ylabel('altitude, $m$')

    top_second_y_axis.grid(True)
    # bug solved by patching .../site-packages/matplotlib/axis.py
    # ref: https://github.com/matplotlib/matplotlib/issues/15621
    top_second_y_axis.yaxis.set_major_locator(ticker.MultipleLocator(base=5))
    top_second_y_axis.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=1))

    inset_altitude = inset_axes(topsubplot,
                                width='10%', height='{}%'.format(10 * gs.get_height_ratios()[1]),
                                bbox_transform=topsubplot.transAxes,  # relative axes coordinates
                                bbox_to_anchor=(0.0, 0.0, 1, 1),  # relative axes coordinates
                                loc=loc)
    rects = LinkedRectangles(topsubplot,
                             Rectangle((0, 0), 0, 0, facecolor='None', edgecolor='red', linewidth=0.5),
                             bottomsubplot,
                             Rectangle((0, 0), 0, 0, facecolor='None', edgecolor='tab:blue', linewidth=0.5))
    rects.r[0].set_bounds(*topsubplot.viewLim.bounds)

    inset_altitude.add_patch(rects.r[0])
    inset_altitude.tick_params(axis='both', which='both',
                               bottom=False, top=False, left=False, right=False,
                               labelbottom=False, labeltop=False, labelleft=False, labelright=False)
    inset_altitude.patch.set_alpha(0.8)
    inset_altitude.spines['bottom'].set_alpha(0.5)
    inset_altitude.spines['top'].set_alpha(0.5)
    inset_altitude.spines['left'].set_alpha(0.5)
    inset_altitude.spines['right'].set_alpha(0.5)

    top_second_x_axis = topsubplot.twiny()
    top_second_x_axis.set_xbound(topsubplot.get_xbound())
    top_second_x_axis.xaxis.set_ticks(x[:nb_hours])
    top_second_x_axis.xaxis.set_major_formatter(ticker.IndexFormatter(x_labels))
    top_second_x_axis.xaxis.set_major_locator(ticker.MultipleLocator(base=1))
    top_second_x_axis.xaxis.set_minor_locator(ticker.AutoMinorLocator(n=6))

    # formatting the bottom (pressure) graph
    bottomsubplot.set_ylim(260, 1100)  # pressure limits of Casio v3
    bottomsubplot.yaxis.set_major_locator(ticker.MultipleLocator(base=10))
    bottomsubplot.yaxis.set_minor_locator(ticker.MultipleLocator(base=1))
    old_ticks = bottomsubplot.get_yticks()
    bottomsubplot.set_yticks(list(old_ticks) + [1013.25])
    bottomsubplot.set_yticklabels(list(map(lambda new: '{:.0f} hPa'.format(new), old_ticks)) + ['MSL$_{ISA}$'])
    bottomsubplot.set_ylim(round(min(z[:nb_hours]) - 5, -1),  # multiple of 10, just below the minimum pressure
                           max(z[:nb_hours]) + 1  # just above maximum pressure
                           )
    bottomsubplot.grid(True, which='major', alpha=0.6)
    bottomsubplot.grid(True, which='minor', alpha=0.3)
    bottomsubplot.xaxis.set_major_formatter(ticker.IndexFormatter(x_labels))
    # bottomsubplot.set_ylabel('')
    inset_pressure = inset_axes(bottomsubplot,
                                width='10%', height='{}%'.format(10 * gs.get_height_ratios()[0]),
                                bbox_transform=bottomsubplot.transAxes,  # relative axes coordinates
                                bbox_to_anchor=(0.0, 0.0, 1, 1),  # relative axes coordinates
                                loc=loc)
    rects.r[1].set_bounds(*bottomsubplot.viewLim.bounds)

    bottomsubplot.callbacks.connect('lim_changed', rects.update)
    bottomsubplot.callbacks.connect('ylim_changed', rects.update)
    topsubplot.callbacks.connect('xlim_changed', rects.update)
    topsubplot.callbacks.connect('ylim_changed', rects.update)

    inset_pressure.add_patch(rects.r[1])
    inset_pressure.tick_params(axis='both', which='both',
                               bottom=False, top=False, left=False, right=False,
                               labelbottom=False, labeltop=False, labelleft=False, labelright=False)

    inset_pressure.patch.set_alpha(0.5)
    inset_pressure.spines['bottom'].set_alpha(0.2)
    inset_pressure.spines['top'].set_alpha(0.2)
    inset_pressure.spines['left'].set_alpha(0.2)
    inset_pressure.spines['right'].set_alpha(0.2)

    # adding curves/points to subplots
    topsubplot.errorbar(x, y, fmt='go', yerr=[lower_err, upper_err], label='Hourly Forecast', markersize=5)
    topsubplot.plot(np.arange(x[0], x[-1], 1 / 60),
                    [v for v in np.polyval(poly, np.arange(x[0], x[-1], 1 / 60))],
                    color='red', linestyle='dotted', alpha=0.5)
    topsubplot.step(np.arange(x[0], x[-1], 1 / 60),
                    [round(v) for v in np.polyval(poly, np.arange(x[0], x[-1], 1 / 60))],
                    color='red', where='post', label='Polynomlal Steps of {}{} degree'.format(degree, '$^{th}$'))
    topsubplot.scatter(now_minutes / 60, 0, color='red', marker='>', label='Fix at {}'.format(strftime('%#H:%M')))
    inset_altitude.plot(x, y, color='red', alpha=0.5)

    bottomsubplot.plot(x, z, color='tab:blue', marker='o', markersize=3.5, label='Atmospheric Pressure', linestyle='--')
    inset_pressure.plot(x, z, color='tab:blue', alpha=0.5)

    # post-processing subplots
    topsubplot.legend()
    bottomsubplot.legend()

    plt.rcParams["savefig.directory"] = None  # To force output in default directories
    plt.savefig(program.GRAPH_FILENAME,  # save first because plt.show() clears the plot
                dpi=program.GRAPH_DPI,
                orientation=program.GRAPH_ORIENTATION,
                papertype=program.GRAPH_PAPERTYPE)

    if not program.PAUSE:
        mng = plt.get_current_fig_manager()
        mng.window.state('zoomed')
        plt.show()

except Exception as e:
    logging.error(traceback.format_exc())
    traceback.print_exc()
    if not args.no_key:
        system('pause')
else:
    if program.PAUSE:
        system('pause')
finally:
    if program.browser.driver.service.process is not None:
        program.browser.quit()
