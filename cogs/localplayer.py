# DISCORD AND CORE
import os, sys, random, discord, typing
from discord.ext import commands

# SPOTIFY
import spotipy
import spotipy.util as util

# YOUTUBE
from youtube_dl import YoutubeDL

# LOCAL FILES
from mutagen.id3 import ID3
from io import BytesIO

'''
    IMPORTANT:
    ffmpeg.exe needs to be in the same directory as bot.py for proper audio streaming
'''

PLAYLIST_FOLDER = os.getenv("PLAYLIST_FOLDER_PATH")

# TRUE or FALSE TO DISABLE SPOTIFY LOOKUPS - requires developer spotify key
if False:
    SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
    SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
    SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
    # spotipy authentication protocol
    spotify = spotipy.Spotify(auth = util.prompt_for_user_token('ramenonsale', 'user-library-read', client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI))


# youtube download options - 
ytdl = YoutubeDL({
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': False,
    'no_warnings': True,
    'youtube_include_dash_manifest': False,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
})

# loads song data for the queue from a playlist file
def loadPlaylist(filepath):
    playlist = []
    # M3U PLAYLIST SUPPORT
    # each line of an .m3u is a file location
    if filepath.endswith('.m3u'):
        with open(filepath, 'r', encoding='utf-8') as playlist_file:
            for file_url in playlist_file.readlines():
                song = loadFileURL(file_url.rstrip())
                if song:
                    playlist.append(song)
    return playlist

# load song data from a single file URL
def loadFileURL(url):
    try:
        data = ID3(url)
        # finding the APIC tag because its not always just 'APIC:'
        for key in data.keys():
            if "APIC:" in key:
                #print(key, f'is the APIC tag for {data["TIT2"]}') #   DEBUG
                pict_key = key
        return {
            'source'        :   'local',
            'url'           :   url,
            'before_options':   None,
            'title'         :   str(data['TIT2']) if 'TIT2' in data else url[url.rindex('\\')+1:-4],
            'info'          :   {
                                    'artist'    :   str(data["TPE1"]) if 'TPE1' in data else None,
                                    'album'     :   str(data["TALB"]) if 'TALB' in data else None,
                                    'pict_data' :   data[pict_key].data if 'pict_key' in locals() else None
                                }
        }
    except Exception as error:
        print(f'\nError Loading Song From Local File URL... {url}\n', type(error), error.args)   # DEBUG

# load song data from a Spotify URL
# url can be a playlist or a single track
def loadSpotifyURL(url):
    try:
        try:
            # spotipy get data from track
            song = spotify.track(url)
            return loadYouTubeURL(f'{song["name"]} - {song["artists"][0]["name"]}')
        except:
            pass
        # spotipy get data from playlist
        songs = spotify.playlist_tracks(url)
        playlist = None
        for i,track in enumerate(songs['items']):
            item = loadYouTubeURL(f'{track["track"]["name"]} - {track["track"]["artists"][0]["name"]}')
            if playlist: 
                playlist.extend(item)
            else:
                playlist = item
        # adding all url results to one array to return
        return playlist
    except Exception as error:
        print(f'\nError Loading Song From Spotify URL... {url}\n', type(error), error.args)   # DEBUG
      

# load song data from a youtube link
# url can be a youtube paylist or a single video
def loadYouTubeURL(url):
    try:
        data = ytdl.extract_info(url, download=False)
        if 'entries' in data: # check if data is from a playlist
            data = data['entries']
        else:
            data = [data]
        #print(data[0].keys())  # DEBUG
        # return mapped song data in an array for each video
        return [
            {
                'source'        :   'youtube',
                'url'           :   video['url'],
                'before_options':   "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                'title'         :   video['title'],
                'video_url'     :   video['webpage_url']
            } for video in data
        ]
    except Exception as error:
        print(f'\nError Loading Song From Video URL... {url}\n', type(error), error.args)   # DEBUG

# parses the information from a song in queue to be sent in discord
def parseSongInfo(song):
    print(f'Parsing Song Info... {song["title"]}')
    if song['source'] == 'local':
        info = {
            'content'   :   f'**Song Title:** {song["title"]}' +
                            ( '' if song["info"]["artist"] == None else '\n**Song Artist: **'+song["info"]["artist"] ) +
                            ( '' if song["info"]["album"] == None else '\n**Album: **'+song["info"]["album"] ) +
                            ( '' if song['info']['pict_data'] != None else '\n**No Song Art Found.**' ),
            'file'      :   None if song['info']['pict_data'] == None else discord.File(BytesIO(song['info']['pict_data']), filename='album_art.png')
        }
    elif song['source'] == 'youtube':
        info = {
            'content'   :   song["video_url"],
            'file'      :   None
        }
    return info


class LocalMusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = []
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('LocalMuiscPlayer loaded.')
    
    # easily readable function to use elsewhere
    async def checkQueueIsEmpty(self, ctx):
        if not self.song_queue:
            await ctx.send('**Queue is Empty.**')
        return not self.song_queue

    # recursive song playing helper function
    def playQueue(self, ctx):
        if self.song_queue:
            song = self.song_queue[0]
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                ctx.voice_client.source = discord.FFmpegPCMAudio(song['url'], before_options=song['before_options'])
            else:
                ctx.voice_client.play(
                    discord.FFmpegPCMAudio(song['url'], before_options=song['before_options']),
                    after=lambda e: [
                        print('playQueue() called upon Song end.'),
                        self.song_queue.pop(0),
                        self.playQueue(ctx)
                    ]
                )
        else:
            print('playQueue() cannot execute due to empty Queue.')

    @commands.command(name='list', aliases=['lists'])
    async def showlist(self, ctx):
        await ctx.send('\n'.join([f[:-4] for f in os.listdir(PLAYLIST_FOLDER)]))

    @commands.command(name='load', aliases=['sload'])
    async def loadsongs(self, ctx, *, playlist_name):
        if playlist_name == '':
            await ctx.send('please include a playlist name.')
        else:
            playlist_files = [f for f in os.listdir(PLAYLIST_FOLDER)]
            playlist_names = [f[:-4] for f in playlist_files]
            if playlist_name in playlist_names:
                playlist = loadPlaylist(PLAYLIST_FOLDER+'\\'+playlist_files[playlist_names.index(playlist_name)])
                if ctx.invoked_with == 'sload':
                    random.shuffle(playlist)
                    print('shuffled playlist.')
                self.song_queue.extend(playlist)
                print('added onto queue.')
                await ctx.send(f'**added** ***{playlist_name}*** **to the queue.**')
            else:
                await ctx.send(f'{playlist_name} is not an available playlist.')


    @commands.command(name='playspotify', aliases=['ps'])
    async def play_spotify(self, ctx, *, url):
        songs = loadSpotifyURL(url)
        self.song_queue.extend(songs)
        await ctx.message.delete()
        if len(songs) == 1:
            await ctx.send(f'**Added {songs[0]["title"]} to the Queue.**')
        else:
            await ctx.send(f'**Added Playlist to the Queue.**')

    @commands.command(name='add')
    async def add_to_queue(self, ctx, *, video):
        songs = loadYouTubeURL(video)
        self.song_queue.extend(songs)
        await ctx.message.delete()
        if len(songs) == 1:
            await ctx.send(f'**Added {songs[0]["title"]} to the Queue.**')
        else:
            await ctx.send(f'**Added Playlist to the Queue.**')
    
    @commands.command(name='shuffle', aliases=['sh'])
    async def shuffle_queue(self, ctx):
        if await self.checkQueueIsEmpty(ctx):
            return
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            song_queue_without_current = self.song_queue[1:]
            random.shuffle(song_queue_without_current)
            self.song_queue = [self.song_queue[0]]
            self.song_queue.extend(song_queue_without_current)
        else:
            random.shuffle(self.song_queue)
        await ctx.send('**Queue Shuffled.**')

    @commands.command(name='pause', aliases=['stop'])
    async def pause_queue(self, ctx):
        if await self.checkQueueIsEmpty(ctx):
            return
        if ctx.voice_client.is_paused() or ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send('**Queue '+ ('Already' if ctx.voice_client.is_paused() else None) +' Paused.**')
        else:
            await ctx.send('**Queue is not Playing.**')

    @commands.command(name='playnow')
    async def playnow(self, ctx, *, arg: typing.Union[int, str]):
        if self.song_queue:
            self.song_queue.pop(0)
        if isinstance(arg, int): # if arg is index
            if arg-1 < 0 or arg-1 > len(self.song_queue):
                await ctx.send(f'**Song Index {arg} is Out of Bounds.**')
                return
            song = self.song_queue.pop(arg-2)
            self.song_queue.insert(0, song)
        else: # arg is video url
            songs = loadYouTubeURL(arg)
            self.song_queue = songs+self.song_queue
            song = self.song_queue[0]
        await ctx.message.delete()
        self.playQueue(ctx)
        await ctx.send(f'**Now Playing >> ** {song["title"]}.')

    @commands.command(name='play', aliases=['start'])
    async def play_queue(self, ctx):
        if await self.checkQueueIsEmpty(ctx):
            return
        song = self.song_queue[0]
        if ctx.voice_client.is_playing():
            await ctx.send(f'**Already Playing >> **{song["title"]}')
        elif ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send(f'**Resuming >> **{song["title"]}')
        else:
            self.playQueue(ctx)
            await ctx.send(f'**Now Playing >> ** {song["title"]}.')
    
    @commands.command(name='skipto')
    async def queue_skipto(self, ctx, index: int = 1):
        if await self.checkQueueIsEmpty(ctx):
            return
        if index < 1 or index > len(self.song_queue):
            await ctx.send(f'**Song Index {index} is Out of Bounds.**')
            return
        for x in range(index-1):
            self.song_queue.pop(0)
        self.playQueue(ctx)
        song = self.song_queue[0]
        await ctx.send(f'**Now Playing >> ** {song["title"]}.')

    @commands.command(name='skip', aliases=['next'])
    async def queue_skip(self, ctx):
        if await self.checkQueueIsEmpty(ctx):
            return
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            self.song_queue.pop(0)
            # TODO another way to handle and empty queue after skip
            try:
                song = self.song_queue[0]
                ctx.voice_client.source = discord.FFmpegPCMAudio(song['url'], before_options=song['before_options'])
                await ctx.send(f'**Skipping.. Now Playing >>** {song["title"]}.')
            except Exception as error:
                print(type(error), error.args)
        else:
            await ctx.send('**Queue is not Playing.**')

    @commands.command(name='info')
    async def queue_info(self, ctx, song_index: int = 1):
        if await self.checkQueueIsEmpty(ctx):
            return
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            song = self.song_queue[song_index-1]
            info = parseSongInfo(song)
            await ctx.send( content=info['content'], file=info['file'] )
        else:
            await ctx.send('**Queue is not Playing.**')

    @commands.command(name='clear', aliases=['empty'])
    async def clear_queue(self, ctx):
        if await self.checkQueueIsEmpty(ctx):
            return
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            self.song_queue = [self.song_queue[0]]
        else:
            self.song_queue = []
        await ctx.send('**Queue Cleared.**')

    @commands.command(name='queue', aliases=['q'])
    async def view_queue(self, ctx, queue_amount: int = 10):
        if await self.checkQueueIsEmpty(ctx):
            return
        queue_list = [song['title'] for song in self.song_queue[0:queue_amount]]
        if ctx.voice_client:
            if ctx.voice_client.is_paused():
                queue_list[0] = "**PAUSED:** "+queue_list[0]
            elif ctx.voice_client.is_playing():
                queue_list[0] = "**PLAYING:** "+queue_list[0]
        queue_list = [str(i+1)+" "+queue_list[i] for i in range(len(queue_list))]
        queue_string = '\n'.join(queue_list)
        await ctx.send(f'**Next {len(queue_list)} Songs in Queue:**\n{queue_string}\n**{len(self.song_queue)} Songs Total in Queue**')
    
    # NERD COMMANDS
    @commands.command(name='mem')
    async def memory_size(self, ctx):
        await ctx.send(f'Queue takes up {convert_bytes(get_size(self.song_queue))} in memory')

# DISCORD COG LOAD AND UNLOAD FUNCTIONS
def setup(bot):
    print('Setting up LocalMediaPlayer.')
    bot.add_cog(LocalMusicPlayer(bot))

def teardown(bot):
    print('Tearing down LocalMediaPlayer.')
    bot.remove_cog('LocalMusicPlayer')







# other cited code from online for memeory helper functions

def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size

def convert_bytes(size):
   for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
       if size < 1024.0:
           return "%3.1f %s" % (size, x)
       size /= 1024.0
   return size