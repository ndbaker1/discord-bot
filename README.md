# discord-bot
A Bot for Discord that can stream a music playlist into a server's voice chat for everyone to listen.<br>
Coded in python using [discordpy](https://discordpy.readthedocs.io/en/latest/) - Python API Wrapper for Discord
## Setup
### Requirements
Python package requirements are located in [requirements.txt](requirements.txt) and can be installed with the command
```
pip install -r requirements.txt
```
Additionally, FFmpeg is used for audio processing so an `ffmpeg.exe` executable will be **required** in the same directory as bot.py
### Environment Variables
Using _python-dotenv_, all personal information used should be kept in a **.env** file that contains the following:
```
# .env contents..

DISCORD_TOKEN = "your bot's token"
PLAYLIST_FOLDER_PATH = "path to a folder that contains a .m3u playlist"

# Spotify info only necessary if you plan to use the spotify lookup found in localplayer.py
SPOTIPY_CLIENT_ID = "your spotify client ID"
SPOTIPY_CLIENT_SECRET = "your spotify client secret"
SPOTIPY_REDIRECT_URI = "your spotify redirect URI"
```
_The line that enables/disables spotify requirements can be found [Here.](cogs/localplayer.py#L23-L24)_

### Usage
_Generic bot commands like:_
| Command | Description |
|---|---|
|join|Connects to the voice channel|
|leave|Disconnects from the voice channel|
|help|Lists all commands|

_The LocalPlayer is capable of the following commands:_
| Command | Description |
|---|---|
|add|Add a playlist or youtube link to the song queue|               
|clear|Clear the song queue|         
|info|Fetch link or Dispaly song information|        
|list|List available local playlists|        
|load|Load a local playlist|             
|pause|Pause the song queue|       
|play|Start playing the song queue|        
|playnow|Play a specific song in queue first|     
|playspotify|Play a song from a spotify playlist| 
|queue|Display the next several songs in queue|
|shuffle|Randomize the order of the songs in queue|
|skip|Skip the currently playing song|        
|skipto|Skip a certain amount of songs in queue|
