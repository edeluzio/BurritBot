from decimal import Decimal
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
import sqldb
import asyncio
import val

client = commands.Bot(command_prefix='.')
poll = []


def check(author):
    def inner_check(message):
        return message.author == author

    return inner_check


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
        if (msg.content == '.update' and channel.name =='burrit-cinemas-ratings'):
            await msg.delete()
        else:
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
    message = ctx.message
    await channel.purge(limit=100)
    message = message.content
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


@client.command()
async def peaklist(ctx):
    try:
        file = open('texts/peaks.txt', 'r')
    except:
        file = open('texts/peaks.txt', 'w')

    l = file.read().split('\n')

    channel = ctx.channel
    peaks = ''
    for person in l:
        if not (person == ' '):
            peaks = peaks + person + '\n'

    embed = discord.Embed(title=("Current Overpeakers:"))
    embed.add_field(name='________________________', value=str(peaks))
    await channel.send(embed=embed)


@client.command()
async def peak(ctx):
    channel = ctx.channel
    message = ctx.message
    message = message.content
    user = re.sub(r'(^.peak)', '', message).lstrip()

    try:
        file = open('texts/peaks.txt', 'r')
    except:
        file = open('texts/peaks.txt', 'w')

    l = file.read().split('\n')

    matching = [s for s in l if (user + ':') in s]

    if matching.__len__() == 0:
        peaks = ''
        for person in l:
            if not (person == ' '):
                peaks = peaks + person + '\n'

        embed = discord.Embed(title=(user + " is not currently in the overpeak system"))
        embed.add_field(name='Current overpeakers:', value=str(peaks))
        embed.add_field(name='To add to overpeaker list:', value=str("Type .addpeak (USER)"))
        await channel.send(embed=embed)

    else:
        list2 = []
        for person in l:
            list2.append(person.split(" "))
        for person in list2:
            if person[0] == (user + ':'):
                count = int(person[1]) + 1

        search = user + ': ' + str(count - 1)
        result = user + ': ' + str(count)

        l.pop(l.index(search))
        l.append(result)
        l = sorted(l)

        filewrite = ''
        for person in l:
            if not (person == ' '):
                filewrite = filewrite + person + '\n'

        file = open('texts/peaks.txt', 'w')
        file.write(filewrite.lstrip())
        embed = discord.Embed(title=(user + " overpeaked again"))
        embed.add_field(name='What a fucking dumbass', value=("He's overpeaked " + str(count) + ' times'))
        await channel.send(embed=embed)


@client.command()
async def addpeak(ctx):
    channel = ctx.channel
    message = ctx.message
    message = message.content
    user = re.sub(r'(^.addpeak)', '', message).lstrip()

    file = open('texts/peaks.txt', 'r')

    l = file.read().split('\n')

    matching = [s for s in l if (user + ':') in s]

    if not matching.__len__() == 0:
        embed = discord.Embed(title=(user + " is already in the list of overpeakers"))
        await channel.send(embed=embed)
    else:
        file = open('texts/peaks.txt', 'a')
        file.write(user + ": " + str(0) + '\n')

        embed = discord.Embed(title=(user + " has been added to the list of overpeakers"))
        await channel.send(embed=embed)


@client.command()
async def valsignup(ctx):
    author = ctx.author
    channel = ctx.channel
    message = ctx.message

    await author.send(
        "Welcome to the Valorant x Burrit database signup.\nOnce signed up, other users can do things like view your shop, MMR, and many more things to come!")

    await author.send("First, respond with your Valorant username (without the #NA1).")
    try:
        valname = await client.wait_for('message', check=check(author), timeout=30.0)
        valname = valname.content
    except asyncio.TimeoutError:
        return await author.send("Sorry, you took too long too respond. Please reenter .valsignup")

    await author.send("Next, respond with your Riot username.")
    try:
        username = await client.wait_for('message', check=check(author), timeout=30.0)
        username = username.content
    except asyncio.TimeoutError:
        return await author.send("Sorry, you took too long too respond. Please reenter .valsignup")


    await author.send(
        "Next, respond with your Valorant password.\nYour password will NOT be saved to the database, but is needed to obtain authorization headers for HTTP requests. You are also free to delete these messages after responding with your password")
    try:
        password = await client.wait_for('message', check=check(author), timeout=30.0)
        password = password.content
    except asyncio.TimeoutError:
        return await author.send("Sorry, you took too long too respond. Please reenter .valsignup")

    # check if val acc/ get val auth stuff
    try:
        vauth = val.auth(username, password)
    except:
        errmsg = "The username: " + username + " and password: " + password + " is not associated with a Riot account. Please reenter .valsignup"
        await author.send(errmsg)
        return

    # check db
    data = {'username': username, 'valname': valname, 'password': password, 'authdata': vauth}
    if sqldb.checkDB(data):
        errmsg = "This user has already signed up in the database"
        await author.send(errmsg)
        return

    # add to db
    else:
        sqldb.addDB(data)

        # say congrats
        return await author.send("You are now registered in the database!")


@client.command()
async def shop(ctx):
    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    valname = re.sub(r'(^.shop)', '', message).lstrip()

    if not (sqldb.checkDB({'valname': valname})):
        embed = discord.Embed(title=(valname.capitalize() + " is not registered in the database"))
        await channel.send(embed=embed)

    else:
        dbinfo = sqldb.getDB({'valname': valname})
        vshop = val.fetchStore(dbinfo)

        fskins = nskins = ''

        index = 0
        for names in vshop['feat']['names']:
            fskins = fskins + names + '\t\t ---- ' + str(vshop['feat']['prices'][index]) + ' VP' + '\n'
            index = index + 1

        index = 0
        for names in vshop['norm']['names']:
            nskins = nskins + names + '\t\t ---- ' + str(vshop['norm']['prices'][index]) + ' VP' + '\n'
            index = index + 1

        bskins = None
        index = 0
        if 'bon' in vshop:
            bskins = ''
            for names in vshop['bon']['names']:
                bskins = bskins + names + '\t\t ---- ' + str(vshop['bon']['prices'][index]) + ' VP' + '\n'
                index = index + 1
        # send message back
        embed = discord.Embed(title=(valname.capitalize() + "'s Valorant Store"))
        embed.add_field(name='Featured Shop', value=fskins, inline=False)
        embed.add_field(name='Regular Shop', value=nskins, inline=False)
        embed.add_field(name='Night Shop', value=bskins or "You currently have no Night Shop", inline=False)
        await channel.send(embed=embed)


@client.command()
async def rank(ctx):

    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    valname = re.sub(r'(^.rank)', '', message).lstrip()

    if not (sqldb.checkDB({'valname': valname})):
        embed = discord.Embed(title=(valname.capitalize()+ " is not registered in the database"))
        await channel.send(embed=embed)
        return;
    else:
        dbinfo = sqldb.getDB({'valname': valname})
        try:
            mmrdata = val.mmr(dbinfo)
        except:
            embed = discord.Embed(title=(valname.capitalize()+ " has not played a competitive game this season"))
            await channel.send(embed=embed)
            return;
        dec = Decimal(10) ** -2
        mmrtotal = mmrdata['wins'] + mmrdata['losses']
        mmrperc = (mmrdata['wins'] / mmrtotal * 100)
        mmrperc = Decimal(mmrperc).quantize(dec)
        mmrperc = str(mmrperc) + '%'

        embed = discord.Embed(title=(valname.capitalize() + "'s current Valorant Rank"))
        embed.add_field(name='Rank', value=mmrdata['rank'])
        embed.add_field(name='Elo in rank', value=mmrdata['elo'], inline=False)
        embed.add_field(name='Net elo from last game played', value=mmrdata['lastGame'])
        embed.add_field(name='Wins', value=mmrdata['wins'], inline=False)
        embed.add_field(name='Losses', value=mmrdata['losses'])
        embed.add_field(name='Win Percentage', value=mmrperc,inline=False)

        await channel.send(embed=embed)


@client.command()
async def pastrank(ctx):
    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    config = re.sub(r'(^.pastrank)', '', message).lstrip()

    config = config.split(' ')



    valname = config[1]
    episode = config[0]
    ea = 'Episode ' + episode[1] + ' Act ' + episode[3] + ' Valorant Rank'
    act = int(episode[3])
    episode = 'EPISODE ' + episode[1]

    if act > 3 or act < 1:
        embed = discord.Embed(title=( + "This is not a valid Act"))
        await channel.send(embed=embed)
        return


    response = requests.get("https://valorant-api.com/v1/seasons")
    seasons = response.json()
    seasons = seasons['data']


    for szns in seasons:
        if szns['displayName'] == episode:
            index = seasons.index(szns) + act

    if not (index):
        print()

    else:
        if not (sqldb.checkDB({'valname': valname})):
            embed = discord.Embed(title=(valname + " is not registered in the database"))
            await channel.send(embed=embed)
            return
        else:
            szn = seasons[index]['uuid']
            dbinfo = sqldb.getDB({'valname': valname})
            mmrdata = val.pastmmr(dbinfo,szn)

            dec = Decimal(10) ** -2
            mmrtotal = mmrdata['wins'] + mmrdata['losses']
            mmrperc = (mmrdata['wins'] / mmrtotal * 100)
            mmrperc = Decimal(mmrperc).quantize(dec)
            mmrperc = str(mmrperc) + '%'

            embed = discord.Embed(title=(valname + "'s " + ea))
            embed.add_field(name='Rank at end of Act', value=mmrdata['rank'])
            embed.add_field(name='Act Rank', value=mmrdata['sznrank'], inline=False)
            embed.add_field(name='Wins', value=mmrdata['wins'], inline=False)
            embed.add_field(name='Losses', value=mmrdata['losses'])
            embed.add_field(name='Win Percentage', value=mmrperc,inline=False)

            await channel.send(embed=embed)


@client.command()
async def users(ctx):
    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content

    embed = discord.Embed(title='Users Currently Registered')
    embed.add_field(name='Database ID', value=sqldb.getAll())
    await channel.send(embed=embed)


client.run('ODM4MTAzNjY5MzcwNjUwNzE1.YI2O3Q.Tuq8ZqrLshUVxyw0Qc2p6_nu-A4')
