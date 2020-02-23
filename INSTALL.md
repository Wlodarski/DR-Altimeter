# Installation

## Windows 

1. Download the precompiled files to a folder of your choice:
   - DR-Altimeter.exe
   - Chromedriver.exe
   
2. Run DR-Altimeter.exe
   - At first run, config.ini will be created and configured with your current latitude and longitude. You'll see briefly an empty Chrome window. It's normal. It's required to acquire your position.
   
3. Edit the congiguration file (config.ini) to fit your need.

4. _Optional_ Configure a Slack bot
   - Create a bot and register it to a chat room
   - Add SLACK_API_TOKEN to windows system environment variables
   - Restart Windows
   - Create a shortcut with the --slack argument pointing to your designated chat room

## Linux and other OS

DR-Altimeter haven't been tested on other os system than Windows 10 running Python 3.6, but it should work with only minor tweeks.

1. Download the Python source files:
   - DR-Altimeter.py
   - forcastarray.py
   - ISA.py
   - txttable.py
   
2. Install all the required librairies:
   - pip install matplotlib numpy slack selenium termcolor colorama

3. Run DR-Altimeter.py and adapt the configuration file, config.ini, generated at first run to suit your need.


## Chromedriver.exe

If you encounter problems with the provided Chromedriver, dowload another version from [Google's repository](https://chromedriver.storage.googleapis.com/index.html). Choose one that matches your current Chrome browser version to maximise compatibility.

