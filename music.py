from youtube_dl import YoutubeDL
import requests
from discord import FFmpegPCMAudio
import discord.utils
from discord.ext import commands
import ffmpeg
import queue

FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
q1 = queue.Queue()


def checkQueue(voice):
    if (q1.qsize() > 0):
        voice.play(FFmpegPCMAudio(queue.get(), **FFMPEG_OPTS), after=checkQueue())
    else:
        return

#Get videos from links or from youtube search
def search(query, song):
    with YoutubeDL({'format': 'bestaudio', 'noplaylist':'True'}) as ydl:
        try: requests.get(song)
        except: info = ydl.extract_info(f"ytsearch:{song}", download=False)['entries'][0]
        else: info = ydl.extract_info(song, download=False)
    return (info, info['formats'][0]['url'])


async def add(ctx, voice, source, song):
    channel = ctx.author.voice.channel
    q1.put(source)

    # join channel
    # print('pring voice stuff:'+ voice.is_connected())
    if voice and voice.is_connected():
        print('voice and is connnected')
        await voice.move_to(channel)
    else:
        print('not connected')
        voice = await channel.connect()
        # play once, then get from queue recursively
        print('now playing' + song)
        voice.play(FFmpegPCMAudio(q1.get(), **FFMPEG_OPTS), after=checkQueue(voice))
        voice.is_playing()
    # grab from queue
    # play 
    # when done, recursively play from queue again

def skip(ctx, voice):
    try:
        voice.stop()
    except Exception as e:
        print(e)
    voice.play(FFmpegPCMAudio(q1.get(), **FFMPEG_OPTS), after=checkQueue(voice))