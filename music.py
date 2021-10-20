from youtube_dl import YoutubeDL
from discord import FFmpegPCMAudio
import discord.utils
from discord.ext import commands
import requests, queue, time, asyncio


FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
q1 = queue.Queue()

def myAfter(client, voice):
    coro = checkQueue(client, voice)
    fut = asyncio.run_coroutine_threadsafe(coro, client.loop)
    try:
        fut.result()
    except Exception as e:
        print(' my after error' , e)
        pass

async def checkQueue(client, voice):
    print('queue size is ',  q1.qsize())
    if (q1.qsize() > 0):
        source = await discord.FFmpegOpusAudio.from_probe(q1.get(), **FFMPEG_OPTS)
        voice.play(source, after=lambda e: myAfter(client, voice))
    else:
        await voice.disconnect()

#Get videos from links or from youtube search
def search(query, song):
    with YoutubeDL({'format': 'bestaudio/best', 'noplaylist':'True'}) as ydl:
        try: requests.get(song)
        except: info = ydl.extract_info(f"ytsearch:{song}", download=False)['entries'][0]
        else: info = ydl.extract_info(song, download=False)
    return (info, info['formats'][0]['url'])


async def add(ctx, voice, source, song, client):
    channel = ctx.author.voice.channel
    textChannel = ctx.channel
    q1.put(source)

    # join channel
    if voice and voice.is_connected():
        await voice.move_to(channel)
        # if connected to channel but not playing anything
        if voice and not voice.is_playing():
            # voice.play(FFmpegPCMAudio(q1.get(), **FFMPEG_OPTS), after=lambda e: myAfter(client, voice))
            embed = discord.Embed(title=("Now playing " + song))
            await textChannel.send(embed=embed)
        else:
            embed = discord.Embed(title=("Added " + song + " to the queue"))
            await textChannel.send(embed=embed)
    else:
        # otherwise join the channel the user is in
        voice = await channel.connect()
        source = await discord.FFmpegOpusAudio.from_probe(q1.get(), **FFMPEG_OPTS)
        voice.play(source, after=lambda e: myAfter(client, voice))
        print('first play')
        # voice.play(FFmpegPCMAudio(q1.get(), **FFMPEG_OPTS), after=lambda e: myAfter(client, voice))
        embed = discord.Embed(title=("Now playing " + song))
        await textChannel.send(embed=embed)
        

async def skip(ctx, voice, client):
    voice.stop()
    if q1.qsize() > 0:
        source = await discord.FFmpegOpusAudio.from_probe(q1.get(), **FFMPEG_OPTS)
        voice.play(source, after=lambda e: myAfter(client, voice))
    else:
        await voice.disconnect()

async def stop(ctx, voice, client):
    voice.stop()
    with q1.mutex:
        q1.queue.clear()
    print('queue has been cleared')