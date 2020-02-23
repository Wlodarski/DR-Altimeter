# DR-Altimeter
Altitude 'Dead Reckoning' for Casio Triple Sensor v.3

##Command line options

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