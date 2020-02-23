# Command Line Options

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

If set, the textual output will be posted to your private [Slack](https://slack.com/) chat room.

By chat room _CTxxxxxxx_ id : `--slack CTU2MKQ5P`

By room _#hashtag_ : `--slack #random`

A **Bot User OAuth Access Token** must be register with the postman and included among the OS system environment variables as SLACK_API_TOKEN. The session needs to be restart (or the computer rebooted) for the environment variable to take effect. See [Create a Slack app and authenticate with Postman](https://api.slack.com/tutorials/slack-apps-and-postman) for more information and a tutorial.

 ![DR Altimeter bot](example/Bot_on_Slack.png)
 
### -v, --verbose
