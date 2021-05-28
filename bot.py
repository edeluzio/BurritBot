import discord
import re
from datetime import datetime
import pytz
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import json
import random
import time

client = commands.Bot(command_prefix='.')
poll = []


def is_me(m):
    return m.author == client.user


def get_rot(title):
    url = 'https://www.rottentomatoes.com/search?search=' + title
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    results = soup.find(id='movies-json')
    data = json.loads(results.contents[0])
    rotscr = data['items'][0]['audienceScore']['score']
    return rotscr


@client.event
async def on_ready():
    print("Bot is ready")


@client.command()
async def update(ctx):


    channel = discord.utils.get(ctx.guild.channels, name="burrit-cinemas-ratings")
    messages = await channel.history(limit=500).flatten()
    tmessages = []
    rankings = []
    rotranks = []
    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    day = now.strftime("%b-%d-%Y %I:%M %p")

    # get all messages from channel history and append each line to total messages list
    for msg in messages:
        lines = msg.content.splitlines()
        for l in lines:
            tmessages.append(l)

    # iterate through each message, get the ranking, add to list of total rankings
    for tmsg in tmessages:

        # first split the movie name, and the rating
        title = ""
        ranks = []

        # parse message to seperate title and ranking
        # print(tmsg)
        match = re.match(r"([\d\.\s]+[a-zA-Z|\s]+)([\d|\.]+)", tmsg, re.I)
        if match:
            title = match.groups()[0]
            result = re.sub(r'([\d]+[\.][\s])', '', title)
            title = result.rstrip()
            ranks.append(match.groups()[1])
            # print(match1.groups())

        mov = [title, ranks]
        # print(mov)

        # if movie hasnt been evaluated yet, add to list. otherwise skip it. also check for blank movie option
        inlist = False
        for i in rankings:
            if mov[0] in i[0]:
                inlist = True

        if not mov[0] == '':
            if not inlist:
                rankings.append(mov)
            else:
                for i in rankings:
                    if mov[0] in i[0]:
                        i[1].append(mov[1][0])

    # get burrit average for each movie
    for film in rankings:
        avgrank = float(0)

        # get sum of ranks
        if not (film[0] == ''):
            for nums in film[1]:
                avgrank = avgrank + float(nums)

            # get average of rank
            avgrank = round(avgrank / film[1].__len__(), 2)

            # append to list
            film.append(avgrank)

        # if blank movie then just delete from list
        else:
            film.remove()

    # sort list based on ratings
    rankings.sort(key=lambda x: x[2], reverse=True)

    # get rotten tomatoes average for each movie
    for film in rankings:
        if not (film[0] == ''):
            try:
                scr = get_rot(film[0])
                scr = scr[0] + "." + scr[1]

                rotranks.append(scr)
            except:
                rotranks.append("N/A")

    # bot deletes old messages and writes new rankings to server
    await channel.purge(limit=100, check=is_me)

    nindex = 1
    rindex = 0
    upd = discord.Embed(title='Burrit Rankings')
    upd.add_field(name='Last updated', value=day)
    ranks = ''
    for film in rankings:
        ranks = ranks + str(nindex) + " - " + film[0] + " ---------| Burrit: " + str(film[2]) + "  |  Average: " + str(
            rotranks[rindex]) + "\n"
        nindex += 1
        rindex += 1

    upd.add_field(name='Current Rankings', value=ranks, inline='false')
    await channel.send(embed=upd)


@client.command()
async def addmov(ctx):
    channel = discord.utils.get(ctx.guild.channels, name="movie-vote")
    message = await channel.history(limit=1).flatten()
    await channel.purge(limit=100)
    message = message[0].content
    parse = re.sub(r'(^.addmov)', '', message).lstrip()
    poll.append(parse)
    indnum = 1
    desc = 'Use .addmov (MOVIE NAME) to add to poll\nUse .randmov to do a random poll\nUse .votemov to do a voting poll\nUse .clearmov to reset the poll'

    final = discord.Embed(title="Current Movie Selection", description=desc, color=0x00ff00)

    for movie in poll:
        final.add_field(name=str(indnum) + '.', value=movie, inline='false')
        indnum += 1

    await channel.send(embed=final)


@client.command()
async def clearmov(ctx):
    channel = discord.utils.get(ctx.guild.channels, name="movie-vote")
    await channel.purge(limit=100)
    poll.clear()


@client.command()
async def votemov(ctx):
    channel = discord.utils.get(ctx.guild.channels, name="movie-vote")
    await channel.purge(limit=1)
    message = discord.utils.get(await channel.history(limit=1).flatten())

    reacts = [
        '1️⃣',
        '2️⃣',
        '3️⃣',
        '4️⃣',
        '5️⃣',
        '6️⃣',
        '7️⃣',
        '8️⃣',
        '9️⃣',
        '🔟',
    ]
    # add reactions
    renum = poll.__len__()
    for movs in range(0, renum, 1):
        await message.add_reaction(reacts[movs])

    count = 60
    embed = discord.Embed(title='Voting begins now')
    embed.add_field(name='Timer', value=str(count))
    mes = await channel.send(embed=embed)
    count = count - 1
    time.sleep(0.9)

    # countdown
    for num in range(count, -1, -1):
        embed2 = discord.Embed(title='Voting begins now')
        embed2.add_field(name='Timer', value=str(count))
        count = count - 1
        await mes.edit(embed=embed2)
        time.sleep(0.9)

    # after time now, so get reactions
    await channel.purge(limit=1)
    vote = discord.utils.get(await channel.history(limit=1).flatten())
    reacts = vote.reactions
    index = 0
    temp = reacts[0]
    tie = []
    tienum = 0

    for r in reacts:
        if tienum < r.count:
            tienum = r.count

    for r in reacts:
        if r.count == tienum:
            tie.append(poll[index])
        index = index + 1
    movie = random.choice(tie)
    await channel.purge(limit=1)
    win = discord.Embed(title='BurritCinemas is pleased to present to you:\n\n' + movie)
    await channel.send(embed=win)


@client.command()
async def randmov(ctx):
    channel = discord.utils.get(ctx.guild.channels, name="movie-vote")
    movie = random.choice(poll)
    poll.clear
    await channel.purge(limit=100, check=is_me)

    # countdown
    count = 10
    embed = discord.Embed(title='Countdown begins now')
    embed.add_field(name='Timer', value=str(count))
    mes = await channel.send(embed=embed)
    count = count - 1
    time.sleep(0.9)
    for i in range(count, -1, -1):
        embed2 = discord.Embed(title='Countdown begins now')
        embed2.add_field(name='Timer', value=str(count))
        count = count - 1
        await mes.edit(embed=embed2)
        time.sleep(0.9)

    await channel.purge(limit=1)
    win = discord.Embed(title='BurritCinemas is pleased to present to you:\n\n' + movie)
    await channel.send(embed=win)


@client.command()
async def burhelp(ctx):
    user = ctx.author
    await user.create_dm()


client.run('ODM4MTAzNjY5MzcwNjUwNzE1.YI2O3Q.Tuq8ZqrLshUVxyw0Qc2p6_nu-A4')
