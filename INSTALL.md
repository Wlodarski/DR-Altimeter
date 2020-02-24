# Installation

## Windows 10

1. Download the [precompiled files](windows/precompiled) to a folder of your choice:
   - DR-Altimeter.exe
   - Chromedriver.exe <sup>[problems?](INSTALL.md#chromedriverexe)
   
2. Run ``DR-Altimeter.exe``
   - At first run, config.ini will be created and configured with your current latitude and longitude. You'll see briefly an empty Chrome window. It's normal. It's required to acquire your position.
   
3. Edit the configuration file, [config.ini](CONFIG.md), to suit your need.

4. _Optional_ Configure a Slack bot
   - Create a bot and register it to a chat room
   - Add SLACK_API_TOKEN to Windows system environment variables
   - Restart Windows
   - Create a shortcut with the [--slack](COMMAND.md#-s---slack) argument pointing to your designated chat room
   - It's also often useful to add [--no-key](COMMAND.md#-n---no-key) to the shortcut
   
#### Chromedriver.exe

If you encounter problems with the provided Chromedriver, download another version from [Google's repository](https://chromedriver.storage.googleapis.com/index.html) or [Chromium.org](https://chromedriver.chromium.org/downloads). Choose one that matches your current Chrome browser version to ensure compatibility.


|[Back to README.md](README.md#Installation)|
|----

## Linux and other OS

DR-Altimeter has not been tested on other operating systems than Windows 10 running Python 3.6, but it should work with other os, only minor tweeks.

1. Download the Python [source files](sources):
   - DR-Altimeter.py
   - forcastarray.py
   - ISA.py
   - txttable.py
   
2. Download the Chromedriver compatible with your OS at [Chromium.org](https://chromedriver.chromium.org/downloads)
   
3. Install all the required librairies:
   - ``pip install matplotlib numpy slack selenium termcolor colorama``

4. Run ``python DR-Altimeter.py`` and adapt the configuration file, [config.ini](CONFIG.md), generated at first run to suit your need.


|[Back to README.md](README.md#Installation)|
|----

