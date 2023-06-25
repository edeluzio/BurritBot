from youtube_dl import YoutubeDL
from discord import FFmpegPCMAudio
import discord.utils
from discord.ext import commands
import requests, queue, time, asyncio


FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
q1 = queue.Queue()

async def myAfter(client, voice):
    coro = checkQueue(client, voice)
    fut = asyncio.run_coroutine_threadsafe(coro, client.loop)
    try:
        fut.result()
    except Exception as e:
        print(' my after error' , e)
        await voice.disconnect()
        pass

async def checkQueue(client, voice):
    print('queue size is ',  q1.qsize())
    if (q1.qsize() > 0):
        source = q1.get()
        voice.play(source, after=lambda e: asyncio.run(myAfter(client, voice)))
    else:
        time = 0
        while True:
            await asyncio.sleep(1)
            time = time + 1
            if voice.is_playing():
                time = 0
            if time >= 60:
                await voice.disconnect()
            if not voice.is_connected():
                break

#Get videos from links or from youtube search
def search(song):
    with YoutubeDL({
        'format': 'bestaudio/best',
        'noplaylist':'True',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        }) as ydl:
        try: requests.get(song)
        except: info = ydl.extract_info(f"ytsearch:{song}", download=False)['entries'][0]
        else: info = ydl.extract_info(song, download=False)
    return (info, info['formats'][0]['url'])


async def add(ctx, voice, source, client, url, urltitle):
    channel = ctx.author.voice.channel
    textChannel = ctx.channel

    if voice and voice.is_connected():
        # bot is connected to a voice channel, so move to the channel the user is in (could be same channel) and queue song
        await voice.move_to(channel)
        q1.put(FFmpegPCMAudio(source, **FFMPEG_OPTS))
            # bot is connected to channel but not playing anything, so play song
        if voice and not voice.is_playing():
            # source = await discord.FFmpegOpusAudio.from_probe(q1.get(), **FFMPEG_OPTS)
            source = q1.get()
            voice.play(source, after=lambda e: asyncio.run(myAfter(client, voice)))
            desc = "Now playing [" + urltitle + "](" + url + ") requested by " + ctx.author.mention
            embed = discord.Embed(description=desc)
            await textChannel.send(embed=embed)
        else:
            # otherwise bot is connected and playing music, so add song to queue
            desc = "Added [" + urltitle + "](" + url + ") to the queue requested by " + ctx.author.mention
            embed = discord.Embed(description=desc)
            await textChannel.send(embed=embed)
    else:
        # otherwise bot is not connected to a voice channel, so connect to the channel the user is in. clear queue in case bot was disconnected with songs in queue.
        with q1.mutex:
            q1.queue.clear()
        q1.put(FFmpegPCMAudio(source, **FFMPEG_OPTS))
        # source = await discord.FFmpegOpusAudio.from_probe(q1.get(), **FFMPEG_OPTS)
        source = q1.get()
        voice = await channel.connect()
        voice.play(source, after=lambda e: asyncio.run(myAfter(client, voice)))
        desc = "Now playing [" + urltitle + "](" + url + ") requested by " + ctx.author.mention
        embed = discord.Embed(description=desc)
        await textChannel.send(embed=embed)
        

async def skip(ctx, voice, client):
    voice.stop()
    if q1.qsize() > 0:
        source = q1.get()
        voice.play(source, after=lambda e: asyncio.run(myAfter(client, voice)))
    else:
        await voice.disconnect()

async def stop(ctx, voice, client):
    voice.stop()
    with q1.mutex:
        q1.queue.clear()
    print('queue has been cleared')