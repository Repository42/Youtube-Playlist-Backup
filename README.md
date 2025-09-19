# Youtube Playlist Backup

Exports youtube playlists to json or tsv.

Doesn't use yt-dlp as that can be unreliable when downloading private playlists

## Google API setup
1) Go create a new project at: https://console.cloud.google.com/

2) Then under the `APIs and services` section search for `YouTube Data API v3` and click `enable`

3) Next click onto the `Credentials` tab and click `Create credentials` then `Create OAuth client ID`

4) After that click `Configure consent screen` then `get started`

5) It will give you a form to fill out just make sure you select `External` under audience and you dont need to give a valid contact email

6) Once you are done with the form click `Create`

7) Now you can create your credentials by clicking `Create OAuth client`

8) Select `Desktop app` and then `Create`

9) When it shows a pop up click `Download JSON` and save it in the same directory as the script under the name `credentials.json`

10) Now you need to go back to the `Audience` tab and under `Test users` click `Add users`

11) Then add your email and click `Save`

12) Install dependencies: `python -m pip install -r requirements.txt`

13) After that extremely convuluted setup process you are ready to run the script: `python youtube_backup.py -v`

14) On your first run it will prompt you to sign into your google account (may open automatically)

15) It will say something like google hasn't verified this app, just click `continue`

16) Now go back to the terminal and complete the setup.

17) You also need to make sure you have created a channel for this script to work otherwise it will produce an error.

18) After you have completed your setup you are all complete.

### Its also recommended to add the script to your crontab.

1) Make script executable: `chmod +x youtube_backup.py`

2) Then run: `crontab -e` 

3) And add this line with a correct file path: `0 0 * * * /path/to/youtube_backup.py --config /path/to/config.json --credentials /path/to/credentials --backup`

## Issues

Make sure you follow the setup completely but if you are still having an problem just raise an issue :-)
