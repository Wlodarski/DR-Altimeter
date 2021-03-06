# Configuration File

A default configuration file, config.ini, is created at first run. 

To rebuild the configuration file, delete config.ini. 
To reset a single setting to its default value, delete it. It will be regenerated at next run.

## Content
```
[USER SETTINGS]
https page = https://blank.org
override url = 
geolocation always on = 0
autosave dpi = 300
autosave orientation = landscape
autosave papertype = letter
autosave png-pdf-eps filename = graph.png
press any key = 1
short timeout = 5
long timeout = 10
verbose = 0
minimum hours = 8
display x hours = 6
latitude =
longitude = 

```
## Description 

**bold** = required, cannot be left empty or missing

#### Timeouts
| Keyword | Note |
| --- | --- |
| **short timeout** | About 5 seconds |
| **long timeout** | Between 10 and 60 seconds |

#### Automatic Save
| Keyword | Note |
| --- | --- |
| **autosave png-pdf-eps filename** | The extension determines whether a PDF, an EPS, or an PNG image file is automatically saved |
| **autosave dpi** | resolution in _dots per inch_ |
| **autosave orientation** | _portrait_ or _landscape_  |
| **autosave papertype** | _letter_ or _legal_  |
| press any key | 0 = no, 1 = yes, default = 0 |

#### Interactive GUI, Pan/Zoom window size
| Keyword | Note |
| --- | --- |
**minimum hours**| Fetch at least n hours of forecast
**display x hours** | How many of the fetched hours will be displayed 

#### Geolocation
| Keyword | Note |
| --- | --- |
latitude | North = dd.dddddd, South = -dd.dddddd
longitude | East = dd.dddddd, West = -dd.dddddd
override url | URL of a specific weather station's hourly forecast page. Always starts with [https://www.wunderground.com/hourly/...](https://www.wunderground.com/hourly/ca/orford/IQUEBECO4)
geolocation always on |  0 = no, 1 = yes, default = 0
**https page** | URL of a random webpage, used to activate Chrome's geolocator

## Note

[Command line options](COMMAND.md) have priority over the configuration file.


|[Back to README.md](README.md#configuration)|
|----
