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

import logging
import traceback
from configparser import ConfigParser
from datetime import datetime, timedelta
from os import system, environ
from pathlib import Path
from platform import python_version, python_version_tuple
from re import search

import colorama
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import slack
from matplotlib.gridspec import GridSpec
from matplotlib.projections import register_projection
from numpy import arange
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from termcolor import colored

from ISA import InternationalStandardAtmosphere
from commandline import CommandLineParser
from curvefit import PolynomialCurveFit, date2dhour
from forecast import Forecast
from graph import NoPanXAxes, MyMatplotlibTools
from translation import Translation
from txttable import PredictionTable
from utils import (
    print80,
    nb_date_changes,
    pretty_polyid,
    cross_platform_leading_zeros_removal as no_leading_zeros,
)

_ = Translation()

FULLNAME = "DR Polynomial Altimeter"
VERSION = "v1.1-alpha"  # TODO: change when ready to release
DESCRIPTION = _("Altitude 'Dead Reckoning' for Casio Triple Sensor v.3")
SHORTNAME = "DR-Altimeter"

command_line_parser = CommandLineParser(
    prog_path=Path(__file__), description=DESCRIPTION, shortname=SHORTNAME, version=VERSION,
)
_.set_lang(command_line_parser)
args = command_line_parser.args
command_line_parser.link_together(
    args.latitude, args.longitude, _("If one is provided, both --latitude and --longitude must be provided"),
)

colorama.init()  # otherwise termcolor won't be fully included at compilation by pyinstaller


class Program:
    __slots__ = [
        "NAME",
        "SHORTNAME",
        "VERSION",
        "DESCRIPTION",
        "STATION_NAME",
        "ELEVATION",
        "P_INITIAL",
        "result",
        "forecast",
        "slack",
        "LOG_FILENAME",
        "CONFIG_FILENAME",
        "CS",
        "cfg",
        "TIMEOUT_T",
        "TIMEOUT",
        "TIMEOUT_LONG_T",
        "TIMEOUT_LONG",
        "GEOLOCATION_ALWAYS_ON_T",
        "GEOLOCATION_ALWAYS_ON",
        "WAIT_FOR_KEY_T",
        "WAIT_FOR_KEY",
        "PAUSE",
        "OVERRIDE_URL_T",
        "OVERRIDE_URL_",
        "OVERRIDE_URL",
        "OVERRIDE_URL_EXISTS",
        "ANY_HTTPS_PAGE_T",
        "ANY_HTTPS_PAGE",
        "GEOLOCATED_URL_T",
        "GEOLOCATED_URL",
        "GRAPH_FILENAME_T",
        "GRAPH_FILENAME",
        "GRAPH_DPI_T",
        "GRAPH_DPI",
        "GRAPH_ORIENTATION_T",
        "GRAPH_ORIENTATION",
        "GRAPH_PAPERTYPE_T",
        "GRAPH_PAPERTYPE",
        "VERBOSE_T",
        "VERBOSE_",
        "VERBOSE",
        "SHOW_X_HOURS_T",
        "SHOW_X_HOURS",
        "MIN_HOURS_T",
        "MIN_HOURS",
        "LATITUDE_T",
        "LATITUDE",
        "LONGITUDE_T",
        "LONGITUDE",
        "MISSING_LATLONG",
        "browser",
    ]

    def __init__(self, fullname: str, version: str, description: str, shortname: str):
        """
        :param fullname: program name
        :param version: program version
        :param description: short description
        :param shortname: short name, mainly for logs
        """

        self.NAME = fullname
        self.SHORTNAME = shortname
        self.VERSION = version
        self.DESCRIPTION = description

        self.STATION_NAME = None
        self.ELEVATION = None
        self.P_INITIAL = None

        self.start_console()

        # starts logging
        self.LOG_FILENAME = self.SHORTNAME + ".log"
        logging.basicConfig(
            filename=self.LOG_FILENAME,
            level=logging.INFO,
            filemode="w",
            format="%(asctime)s %(levelname)s : %(message)s",
            datefmt="%Y-%m-%d %H:%M",
        )

        self.result = PredictionTable()
        self.forecast = Forecast()
        self.slack = slack.WebClient(token=environ["SLACK_API_TOKEN"])

        # reads configuration file and recreates missing values
        self.CONFIG_FILENAME = "config.ini"
        self.CS = "USER SETTINGS"
        self.cfg = ConfigParser()
        self.cfg.read(self.CONFIG_FILENAME)

        if self.CS not in self.cfg.sections():
            print80(_("Regenerating {}").format(self.CONFIG_FILENAME))
            print()
            self.cfg.add_section(self.CS)

        self.TIMEOUT_T = "short timeout"
        self.TIMEOUT = int(self.cfg.get(self.CS, self.TIMEOUT_T, fallback="5"))

        self.TIMEOUT_LONG_T = "long timeout"
        self.TIMEOUT_LONG = int(self.cfg.get(self.CS, self.TIMEOUT_LONG_T, fallback="10"))

        self.GEOLOCATION_ALWAYS_ON_T = "geolocation always on"
        self.GEOLOCATION_ALWAYS_ON = bool(int(self.cfg.get(self.CS, self.GEOLOCATION_ALWAYS_ON_T, fallback="0")))

        self.WAIT_FOR_KEY_T = "press any key"
        self.WAIT_FOR_KEY = bool(int(self.cfg.get(self.CS, self.WAIT_FOR_KEY_T, fallback="1")))
        self.PAUSE = (not args.no_key) and self.WAIT_FOR_KEY

        self.OVERRIDE_URL_T = "override url"
        self.OVERRIDE_URL_ = self.cfg.get(self.CS, self.OVERRIDE_URL_T, fallback="")
        if args.override_url is not None:
            self.OVERRIDE_URL = args.override_url
        else:
            self.OVERRIDE_URL = self.OVERRIDE_URL_

        self.OVERRIDE_URL_EXISTS = self.OVERRIDE_URL is not None and self.OVERRIDE_URL.startswith(
            "https://www.wunderground.com/hourly/"
        )

        self.ANY_HTTPS_PAGE_T = "https page"
        self.ANY_HTTPS_PAGE = self.cfg.get(self.CS, self.ANY_HTTPS_PAGE_T, fallback="https://blank.org")

        self.GEOLOCATED_URL_T = "wunderground hourly url"
        self.GEOLOCATED_URL = self.cfg.get(
            self.CS, self.GEOLOCATED_URL_T, fallback="https://www.wunderground.com/hourly/ca/location/",
        )

        self.GRAPH_FILENAME_T = "autosave png-pdf-eps filename"
        self.GRAPH_FILENAME = self.cfg.get(self.CS, self.GRAPH_FILENAME_T, fallback="graph.png")

        self.GRAPH_DPI_T = "autosave dpi"
        self.GRAPH_DPI = int(self.cfg.get(self.CS, self.GRAPH_DPI_T, fallback="600"))

        self.GRAPH_ORIENTATION_T = "autosave orientation"
        self.GRAPH_ORIENTATION = self.cfg.get(self.CS, self.GRAPH_ORIENTATION_T, fallback="landscape")

        self.GRAPH_PAPERTYPE_T = "autosave papertype"
        self.GRAPH_PAPERTYPE = self.cfg.get(self.CS, self.GRAPH_PAPERTYPE_T, fallback="letter")

        self.VERBOSE_T = "verbose"
        self.VERBOSE_ = bool(int(self.cfg.get(self.CS, self.VERBOSE_T, fallback="0")))
        self.VERBOSE = self.VERBOSE_ or args.verbose

        self.SHOW_X_HOURS_T = "display x hours"
        self.SHOW_X_HOURS = max(int(self.cfg.get(self.CS, self.SHOW_X_HOURS_T, fallback="6")), 1)

        self.MIN_HOURS_T = "minimum hours"
        self.MIN_HOURS = max(int(self.cfg.get(self.CS, self.MIN_HOURS_T, fallback="8")), self.SHOW_X_HOURS,)

        self.save_ini()  # save immediately to renew all required values

        # optional values that can be missing
        self.LATITUDE_T = "latitude"
        self.LONGITUDE_T = "longitude"
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

    def start_console(self):
        """
        Open OS console for stdout
        :return: 
        """
        system("title {} {} (Python {})".format(self.NAME, self.VERSION, python_version()))

        print80(colored("{} {}".format(self.NAME, self.VERSION), attrs=["bold"],))
        print80(self.DESCRIPTION)
        print()

        major, minor, patchlevel = map(int, python_version_tuple())
        if major != 3 or minor < 6:
            print80(_("{} works best with Python version 3.6 and above. Please consider updating.").format(self.NAME))
            print()

    def save_ini(self):
        # fmt: off
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
        # fmt: on

        with open(self.CONFIG_FILENAME, "w") as configfile:
            self.cfg.write(configfile)

    def save_lat_lon(self, pos):
        self.cfg.set(self.CS, self.LATITUDE_T, str(pos["latitude"]))
        self.cfg.set(self.CS, self.LONGITUDE_T, str(pos["longitude"]))
        self.save_ini()

        print80(_("Latitude : {:.7f}").format(pos["latitude"]))
        print80(_("Longitude : {:.7f}").format(pos["longitude"]))
        print80(_("Accuracy : {}m").format(pos["accuracy"]))
        logging.info("{:.7f} {:.7f} ±{}m".format(pos["latitude"], pos["longitude"], pos["accuracy"]))
        print()

    def hourly_forecast_url(self):
        if self.GEOLOCATION_ALWAYS_ON or (self.MISSING_LATLONG and not self.OVERRIDE_URL_EXISTS):

            self.browser.go_to(webpage=self.ANY_HTTPS_PAGE, geolocation=True)
            position = self.browser.get_lat_lon()
            self.save_lat_lon(pos=position)
            self.browser.quit()

            #  decreased precision (3 digits instead of 7) to partially preserve anonymity
            _hourly_forecast_url = self.GEOLOCATED_URL + "{:.3f},{:.3f}".format(
                position["latitude"], position["longitude"]
            )

        elif self.OVERRIDE_URL_EXISTS:

            print80(_("Using override URL"))
            _hourly_forecast_url = self.OVERRIDE_URL

        elif not self.MISSING_LATLONG:

            if args.latitude is None:
                print80(_("Using Lat/Lon found in {}").format(self.CONFIG_FILENAME))
            print80(_("Latitude: {}").format(self.LATITUDE))
            print80(_("Longitude: {}").format(self.LONGITUDE))
            print()
            #  decreased precision (3 digits instead of 7) to partially preserve anonymity
            _hourly_forecast_url = self.GEOLOCATED_URL + "{:.3f},{:.3f}".format(self.LATITUDE, self.LONGITUDE)

        else:  # if everything fails, an example url
            _hourly_forecast_url = "https://www.wunderground.com/hourly/ca/montreal/IMONTR15"

        return _hourly_forecast_url

    def check_page(self, title: str):
        """ Make sure we are on the right page by checking the title"""
        try:
            assert title in self.browser.driver.title
        except AssertionError:
            raise NameError(_("Page with wrong title"))

        print80(_("Connected to Wunderground"))

    def wait_until_page_is_loaded(self):
        try:
            WebDriverWait(self.browser.driver, self.TIMEOUT).until(
                ec.presence_of_element_located((By.ID, "hourly-forecast-table"))
            )
            print80(_("Page is ready"))
        except TimeoutException:
            raise TimeoutException(_("Page took too much time to load"))

    def switch_to_metric(self):
        print80(_("Switching to metric"))
        self.browser.driver.find_element_by_id("wuSettings").click()
        self.browser.driver.find_element_by_css_selector("[title^='Switch to Metric'").click()
        try:
            WebDriverWait(self.browser.driver, self.TIMEOUT_LONG).until(
                ec.text_to_be_present_in_element((By.ID, "hourly-forecast-table"), "hPa")
            )
        except TimeoutException:
            raise TimeoutException(_("Unable to switch to metric"))

    def click_next(self):
        self.browser.driver.find_element_by_xpath('//*[@id="nextForecasts"]/span[2]/button').click()

    def get_station_name(self):
        try:
            _elem = self.browser.driver.find_element_by_xpath(
                '//*[@id="inner-content"]/div[2]/lib-city-header/div[1]/div/div/a[1]'
            )
            _st = search("^-?[0-9]* (.*)$", _elem.text)
            self.STATION_NAME = _st.group(1).strip()
        except NoSuchElementException:
            print80(self.register_error(_("Station name not found")))
        if self.STATION_NAME is None or self.STATION_NAME == "STATION":
            try:
                _elem = self.browser.driver.find_element_by_xpath(
                    '//*[@id="inner-content"]/div[2]/lib-city-header/div[1]/div/h1'
                )
                self.STATION_NAME = _elem.text[:20].lstrip(", ") + "..."
            except NoSuchElementException:
                self.STATION_NAME = _("UNKNOWN")
        logging.info(self.STATION_NAME)
        print()
        print80(colored(self.STATION_NAME, attrs=["bold"]))

    def get_atm_pressure_at_station(self):
        _elem = self.browser.driver.find_element_by_xpath(
            '//*[@id="inner-content"]/div[3]/div[2]/div/div[1]'
            "/div[1]/lib-additional-conditions/lib-item-box/div/"
            "div[2]/div/div[1]/div[2]/lib-display-unit/span/span[1]"
        )
        self.P_INITIAL = float(_elem.text)
        print80(
            self.register_info(
                _("Current atmospheric pressure : {} hPa (ISA={:0.1f}m)").format(
                    self.P_INITIAL, isa.altitude(pressure=self.P_INITIAL)
                )
            )
        )
        return self.P_INITIAL

    def get_obs_time(self):
        _elem = self.browser.driver.find_element(By.XPATH, '//*[@id="app-root-state"]')
        _st = search("obsTimeLocal&q;:&q;(....-..-.. ..:..:..)&q;", _elem.get_attribute("innerHTML"),)
        if _st is not None:
            return datetime.strptime(_st.group(1), "%Y-%m-%d %H:%M:%S")
        else:
            print80(self.register_error(_("Observation time not found.")))
            return datetime.now()

    def get_station_elevation(self):
        try:
            _elem = self.browser.driver.find_element(
                By.XPATH, '//*[@id="inner-content"]/div[2]' "/lib-city-header/div[1]/div/span/span/strong",
            )
            self.ELEVATION = int(_elem.text)
        except NoSuchElementException:
            print80(self.register_error(_("Elevation not found. Assuming it to be zero")))
            self.ELEVATION = 0
        print80(
            self.register_info(
                _("Weather station elevation : {}m (ISA={:7.2f}hPa)").format(
                    self.ELEVATION, isa.pressure(altitude=self.ELEVATION)
                )
            )
        )

    def display_results(self):
        _txt = (
            self.result.display_table()
            + "\n==============================================================================="
        )
        logging.info("\n\n" + _txt)
        print(_txt)

    def send_to_slack(self, _fix_hour):
        _txt = self.result.display_table()
        _title = "{}-{:}".format(self.STATION_NAME, _fix_hour.strftime("%Y%m%d-%H%M")).replace(" ", "_")
        _comment = "{} ({}m)\n\n".format(self.STATION_NAME, self.ELEVATION)
        try:
            print80(_("Sending timetable to Slack channel {}").format(args.slack))
            _response = self.slack.files_upload(
                content=_txt, channels=args.slack, title=_title, filename=_title + ".txt", initial_comment=_comment,
            )
            assert _response["ok"]
            print80(_("Sending {} to Slack channel {}").format(program.GRAPH_FILENAME, args.slack))
            _response = self.slack.files_upload(
                file=program.GRAPH_FILENAME,
                channels=args.slack,
                title=_title,
                filename=_title + "." + program.GRAPH_FILENAME.split(".")[-1],
                initial_comment=_comment,
            )
            assert _response["ok"]
        except AssertionError:
            print80(self.register_error(_("Sending to Slack failed")))

    @staticmethod
    def register_info(msg):
        logging.info(msg=msg)
        return msg

    @staticmethod
    def register_error(msg):
        logging.error(msg)
        return msg


class ChromeBrowser:
    """ Controls *chromedriver.exe* """

    __slots__ = ["options", "driver"]

    def __init__(self):
        self.options = Options()
        self._listening_on_disabled()
        self.driver = None

    def _listening_on_disabled(self):
        self.options.add_argument("--log-level=3")
        self.options.add_experimental_option("excludeSwitches", ["enable-logging"])

    def go_to(self, webpage: Path, hidden: bool = False, geolocation: bool = False):
        """ Open browser """
        self.options.add_experimental_option("prefs", {"geolocation": geolocation})
        if hidden and not geolocation:  # geolocation only works if not headless
            self.options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=self.options)
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
            "var done = arguments[0]; " "navigator.geolocation.getCurrentPosition(function (pos){done(pos.coords);});"
        )
        self.close_window()

        return _position


# =====================================================================
#  MAIN
# =====================================================================

program = Program(fullname=FULLNAME, version=VERSION, description=_(DESCRIPTION), shortname=SHORTNAME)
isa = InternationalStandardAtmosphere()

# noinspection PyBroadException
try:
    # ----------------------------------------------------------------------
    # SCRUB HOURLY PREDICTION ON WUNDERGROUND
    # ----------------------------------------------------------------------
    hourly_forecast_url = program.hourly_forecast_url()

    first_day = datetime.today()
    same_day = 1
    if datetime.now().hour == 23:  # https://github.com/Wlodarski/DR-Altimeter/issues/6
        first_day += timedelta(days=1)
        same_day = 0
    last_day = first_day + timedelta(hours=program.MIN_HOURS)
    nth_days = range(0, same_day + nb_date_changes(first_day, last_day))
    dates = [first_day.date() + timedelta(days=day) for day in nth_days]

    first_page = True
    for d in dates:
        date_str = d.strftime("%Y-%m-%d")
        url = hourly_forecast_url + "/date/" + date_str
        if program.VERBOSE:
            print80(url)
        if first_page:
            program.browser.go_to(webpage=url, hidden=True)
            program.check_page(title="Hourly Weather Forecast | Weather Underground")
            program.wait_until_page_is_loaded()
            program.switch_to_metric()
            first_page = False
        else:
            program.click_next()

        if program.STATION_NAME is None:
            program.get_station_name()
        if program.ELEVATION is None:
            program.get_station_elevation()
        if program.P_INITIAL is None:
            program.forecast.add(time=program.get_obs_time(), pressure=program.get_atm_pressure_at_station())
            print()

        elem = program.browser.driver.find_element(By.ID, "hourly-forecast-table")
        for row in elem.text.split("\n"):
            if not row.startswith("Time"):  # skips the header row, which starts with the word Time

                # parsing out hour and predicted pressure
                st = search("^([0-9]+:00 [ap]m).* (.*) hPa$", row)
                hour = datetime.strptime(date_str + " " + st.group(1), "%Y-%m-%d %I:%M %p")
                pressure = float(st.group(2).replace(",", ""))
                program.forecast.add(time=hour, pressure=pressure)

    program.browser.quit()

    # ----------------------------------------------------------------------
    # TRANSLATE PREDICTED PRESSURE INTO PREDICTED ALTITUDE CHANGES
    # ----------------------------------------------------------------------

    program.forecast.reorder_chronologically()  # superfluous but doing anyway, just in case

    fix_hour = datetime.now()  # fix hour set at this specific execution time : after scrub is done

    times = program.forecast.times()
    start = times[0]
    end = times[-1]
    start_full_hour = start.replace(microsecond=0, second=0, minute=0)
    end_full_hour = end.replace(microsecond=0, second=0, minute=0)
    middle_full_hours = arange(start_full_hour + timedelta(hours=1), end_full_hour, timedelta(hours=1)).astype(datetime)

    x = [date2dhour(start_full_hour, t) for t in program.forecast.times()]  # time since start
    y = program.forecast.delta_altitudes(p_ref=program.P_INITIAL)  # altitude change
    z = program.forecast.pressures()  # predicted atmospheric pressure

    # ----------------------------------------------------------------------
    # POLYNOMIAL CURVE FIT
    # ----------------------------------------------------------------------

    if program.VERBOSE:
        print(program.register_info(_(" POLYNOMIAL CURVE FIT ").center(79, "=")))
        print()

    curvefit = PolynomialCurveFit(x, y)

    if program.VERBOSE:
        formula = pretty_polyid(
            polynomial=curvefit.poly, f_text=_("altitude(time)"), var_symbol=_("time"), equal_sign="=",
        )
        print80(program.register_info(_("Degree : {}").format(curvefit.degree)))
        print()
        print80(program.register_info(_("Coefficients : {}").format(curvefit.poly)))
        print()
        print80(program.register_info(_("Time vector (x) : {}").format(x)))
        print()
        print80(program.register_info(_("Altitude vector (y) : {}").format(y)))
        print()
        print80(program.register_info(_("Pressure vector (z) : {}").format(z)))
        print()
        print(program.register_info("\n{}\n".format(formula)))
        print(program.register_info("".center(79, "-")))
        print()

    # ----------------------------------------------------------------------
    # TEXT OUTPUT
    # ----------------------------------------------------------------------

    curvefit.compute_steps(ref_hour=start_full_hour, start=start, fix_hour=fix_hour)

    program.result.add_start(
        hour=start.hour, minute=start.minute, pressure=program.P_INITIAL, times=[curvefit.step_text(start_full_hour)],
    )
    previous_pressure = program.P_INITIAL

    for loop_hour in middle_full_hours:
        if loop_hour in times:

            this_pressure = program.forecast.get_pressure(loop_hour)
            program.result.add(
                hour=loop_hour.hour,
                pressure=this_pressure,
                alt=program.forecast.get_delta_altitude(loop_hour, p_ref=program.P_INITIAL),
                alt_h=program.forecast.get_delta_altitude(loop_hour, p_ref=previous_pressure),
                times=[curvefit.step_text(loop_hour)],
            )
            previous_pressure = this_pressure

        else:
            program.result.add(
                hour=loop_hour.hour, pressure=None, alt=None, alt_h=None, times=[curvefit.step_text(loop_hour)],
            )

    program.result.add(
        hour=end.hour,
        pressure=program.forecast.get_pressure(end),
        alt=program.forecast.get_delta_altitude(end, p_ref=program.P_INITIAL),
        alt_h=program.forecast.get_delta_altitude(end, p_ref=previous_pressure),
        times=[],
    )

    program.display_results()

    # --------------------------------------------------------------------------
    # GRAPH
    # --------------------------------------------------------------------------

    visible_hours = min(program.SHOW_X_HOURS + 1, len(x))
    visible_full_hour = start_full_hour + timedelta(hours=visible_hours)

    mtools = MyMatplotlibTools()
    register_projection(NoPanXAxes)

    # one figure
    fig = plt.figure(
        # fmt: off
        dpi=96, figsize=(16, 9),
        num="{} {}".format(program.STATION_NAME, fix_hour.strftime('%Y%m%d-%H%M')),
        # fmt: on
    )
    plt.figtext(
        # fmt: off
        0.95, 0.01,
        "{} {}".format(program.NAME, program.VERSION),
        horizontalalignment="right", alpha=0.8, fontsize="x-small",
        # fmt: on
    )

    # two subplots on a grid system
    gs = GridSpec(figure=fig, ncols=1, nrows=2, height_ratios=[3, 1], hspace=0.1, bottom=0.07)
    topsubplot = fig.add_subplot(
        gs[0], title="{} ― {}".format(program.STATION_NAME, fix_hour.strftime("%Y.%m.%d %H:%M")),
    )
    bottomsubplot = fig.add_subplot(gs[1], sharex=topsubplot, projection="No Pan X Axes")

    # formatting the top (altitude) graph
    margin = 15
    topsubplot.set_xlim(start - timedelta(minutes=margin + 5), visible_full_hour + timedelta(minutes=margin + 5))
    mtools.set_ylimits(topsubplot, y, visible_hours)
    topsubplot.set_ylabel(_("$\Delta$altitude, $m$"))
    top_second_x_axis = mtools.format_date_ticks(topsubplot)
    top_second_y_axis = mtools.format_altitude_tick(topsubplot, shift=program.ELEVATION)
    top_second_y_axis.set_ylabel(_("altitude, $m$"))
    mtools.set_grid(topsubplot)
    loc = "lower right"
    inset_altitude, rects = mtools.create_inset(topsubplot, bottomsubplot, gs, loc)

    # formatting the bottom (pressure) graph
    bottomsubplot.set_ylim(260, 1100)  # pressure limits of Casio v3

    scale = (max(z) - min(z)) // 5
    if scale > 5:
        base = 20
    elif scale > 2:
        base = 10
    else:
        base = 5

    bottomsubplot.yaxis.set_major_locator(ticker.MultipleLocator(base=base))
    bottomsubplot.yaxis.set_minor_locator(ticker.MultipleLocator(base=1))
    old_ticks = bottomsubplot.get_yticks()
    bottomsubplot.set_yticks(list(old_ticks) + [1013.25])
    bottomsubplot.set_yticklabels(list(map(lambda new: "{:.0f} hPa".format(new), old_ticks)) + ["MSL$_{ISA}$"])
    bottomsubplot.set_ylim(  # multiple of 5, just below the minimum pressure and just above maximum pressure
        # fmt: off
        round(2 * (min(z) - 2.5), -1) // 2,
        round(2 * (max(z) + 2.5), -1) // 2,
        # fmt: on
    )

    mtools.set_grid(bottomsubplot)
    inset_pressure = mtools.add_inset(topsubplot, bottomsubplot, rects, gs, loc)

    # adding curves/points to subplots
    topsubplot.errorbar(
        # fmt: off
        "time", "altitude", yerr="error", data=curvefit.prediction_dict(ref_hour=start_full_hour),
        color="green", marker="o", linestyle="none", markersize=5,
        label=_("Hourly Forecast"),
        zorder=10,
        # fmt: on
    )

    topsubplot.plot(
        # fmt: off
        "time", "dotted line", data=curvefit.curvefit_dict(start_full_hour, margin=margin),
        color="red", marker="", linestyle="dotted",
        label="_nolegend_",
        zorder=8,
        # fmt: on
    )

    topsubplot.step(
        # fmt: off
        "time", "steps", data=curvefit.curvefit_dict(start_full_hour, margin=0),
        where="post",
        color="red", marker="", linestyle="solid",
        label=_("Polynomial Regression of degree {}").format(curvefit.degree),
        zorder=9,
        # fmt: on
    )

    topsubplot.scatter(
        # fmt: off
        fix_hour, 0,
        color="black", marker=9,
        label=_("Fix at {}").format(no_leading_zeros(fix_hour.strftime('#%H:%M'))),
        zorder=11,
        # fmt: on
    )

    inset_altitude.plot(
        # fmt: off
        times, y,
        color="red", alpha=0.95,
        picker=lambda hit, evt: (True, {"inset": "altitude"}),
        # fmt: on
    )

    bottomsubplot.plot(
        # fmt: off
        times, z,
        color="tab:blue", marker="o", markersize=3.5, linestyle="--",
        label=_("Atmospheric Pressure"),
        # fmt: on
    )

    inset_pressure.plot(
        # fmt: off
        times, z,
        color="tab:blue", alpha=0.95,
        picker=lambda hit, evt: (True, {"inset": "pressure"}),
        # fmt: on
    )

    # post-processing subplots
    topsubplot.legend()
    bottomsubplot.legend()

    zoom_saved = None

    def toggle_zoom(_):
        global zoom_saved
        if zoom_saved is None:
            zoom_saved = (topsubplot.get_xlim(), topsubplot.get_ylim())
            topsubplot.autoscale(True)
            fig.canvas.draw_idle()
        else:
            topsubplot.autoscale(False)
            topsubplot.set_xlim(zoom_saved[0])
            topsubplot.set_ylim(zoom_saved[1])
            fig.canvas.draw_idle()
            zoom_saved = None

    def hover(event):
        inset_altitude.set_label("hover")
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("pick_event", toggle_zoom)
    fig.canvas.mpl_connect("motion_notify_event", hover)

    plt.rcParams["savefig.directory"] = None  # To force output in default directories
    plt.savefig(  # save first because plt.show() clears the plot
        program.GRAPH_FILENAME,
        bbox_inches="tight" if args.slack is not None else None,
        dpi=program.GRAPH_DPI,
        orientation=program.GRAPH_ORIENTATION,
        papertype=program.GRAPH_PAPERTYPE,
    )

    if args.slack is not None:
        program.send_to_slack(fix_hour)

    if not args.no_key:
        mng = plt.get_current_fig_manager()
        mng.window.state("zoomed")
        plt.show()

# ----------------------------------------------------------------------
# CLEAN UP
# ----------------------------------------------------------------------
except Exception as e:
    logging.error(traceback.format_exc())
    traceback.print_exc()
    if not args.no_key:
        system("pause")
else:
    if program.PAUSE:
        system("pause")
finally:
    if program.browser.driver.service.process is not None:
        program.browser.quit()
