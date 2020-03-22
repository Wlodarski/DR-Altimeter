# Installation

## Windows 10

1. Download and extract the [latest .zip release](https://github.com/Wlodarski/DR-Altimeter/releases/latest) to a folder of your choice:
     - DR-Altimeter.exe
     - Chromedriver.exe <sup>[problems?](INSTALL.md#chromedriverexe)
     - LICENSE.md and the documentation files (*.md)
   
2. Run ``DR-Altimeter.exe`` .
   - At first run, config.ini will be created and configured with your current latitude and longitude. You'll see briefly an empty Chrome window. It's normal. It's required to acquire your position.
   
3. Edit the configuration file, [config.ini](CONFIG.md), to suit your need.

4. _Optional_ Configure a Slack bot:
   - Create a bot and register it to a chat room
   - Add SLACK_API_TOKEN to Windows system environment variables
   - Restart Windows
   - Create a shortcut with the [--slack](COMMAND.md#-s---slack) argument pointing to your designated chat room
   - It's also often useful to add [--no-key](COMMAND.md#-n---no-key) to the shortcut
   
#### Chromedriver.exe

If you encounter problems with the provided Chrome driver, download another version from [Chromium.org](https://chromedriver.chromium.org/downloads). Choose one that matches your current Chrome browser version to ensure compatibility.


|[Back to README.md](README.md#Installation)|
|----

## Linux and other OS

DR-Altimeter has not been tested on operating systems other than Windows 10 running Python 3.6, but it should work with only minor tweaks. Python version 3.6 or above is strongly recommended, but it should be usable with version 3.2 and above.

1. Download the Python [source files](src):
   - DR-Altimeter.py
   - ISA.py
   - commandline.py
   - curvefit.py
   - forecast.py
   - graph.py
   - translation.py
   - txttable.py
   - utils.py
   - ...
   
2. Download the Chrome driver compatible with your OS at [Chromium.org](https://chromedriver.chromium.org/downloads)
   
3. Install all the required libraries:
   - ``pip install matplotlib numpy slack selenium termcolor colorama texttable [pathlib, ...]``

4. Run ``python DR-Altimeter.py`` and adapt the configuration file, [config.ini](CONFIG.md), generated at first run to suit your need.


|[Back to README.md](README.md#Installation)|
|----

