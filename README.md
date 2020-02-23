# DR-Altimeter
Altitude 'Dead Reckoning' for Casio Triple Sensor v.3

![graph](example/graph_example.png)

## Config.ini

To regenerate the configuration file, delete config.ini. A new one will be recreated with default values.

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

| Keyword | Note |
| --- | --- |
| short timeout |  |
| long timeout |  |
| autosave png-pdf-eps filename | The extension determines twhether a PDF, an EPS, or an PNG image file is automatically saved |
| autosave dpi | dot per inch |
| autosave orientation | _portrait_ or _landscape_  |
| autosave papertype | _letter_ or _legal_  |


## Command line options

***Command lines options take precedence over *config.ini* settings***

### -n, --no-key 

**Disables "*Press any key*" pauses.** 

Useful to automate execution without user intervention

### --latitude, --longitude

Somewhere in New York City : `--latitude 40.730610 --longitude -73.935242`

### --override-url

URL of a specific weather station's hourly forecast page. Always starts with 'https://www.wunderground.com/hourly/...

Ocean Hill, Brooklin Station : `--override-url https://www.wunderground.com/hourly/us/ny/new-york%20city/KNYNEWYO736
`
### -s, --slack

If provided, a summary will be posted on [Slack](https://slack.com/).

By chat room id : `--slack CTU2MKQ5P`

By room hashtag : `--slack #random`

A **Bot User OAuth Access Token** must be register with the postman and included among the OS system environment variables as SLACK_API_TOKEN. The session needs to be restart (or the computer rebooted) for the environment variable to take effect. See [Create a Slack app and authenticate with Postman](https://api.slack.com/tutorials/slack-apps-and-postman)
 
 
### -v, --verbose
