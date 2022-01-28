from decimal import Decimal
from datetime import datetime
from discord.ext import commands
from bs4 import BeautifulSoup
import requests, pytz, discord, re, json, random, time, sqldb, asyncio, val, music, traceback

intents = discord.Intents().all()
client = commands.Bot(command_prefix='.', intents=intents)
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
    win = discord.Embed(description='BurritCinemas is pleased to present to you:\n\n' + movie)
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

    # kross and mark check cuz he sucks
    # if (valname.lower() == 'empty'):
    #
    #     # countdown
    #     count = 60
    #     embed = discord.Embed(description=("Looks we got a nongamer here! Guess you're gonna have to wait on your shop bitch"))
    #     embed.add_field(name='Timer', value=str(count))
    #     mes = await channel.send(embed=embed)
    #     count = count - 1
    #     time.sleep(0.9)
    #     for i in range(count, -1, -1):
    #         embed2 = discord.Embed(description="Looks we got a nongamer here! Guess you're gonna have to wait on your shop bitch")
    #         embed2.add_field(name='Timer', value=str(count))
    #         count = count - 1
    #         await mes.edit(embed=embed2)
    #         time.sleep(0.9)
        # await channel.send(embed=embed)

    if not (sqldb.checkDB({'valname': valname})):
        embed = discord.Embed(description=(valname.capitalize() + " is not registered in the database"))
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
        embed = discord.Embed(description=(valname.capitalize()+ " is not registered in the database"))
        await channel.send(embed=embed)
        return
    else:
        dbinfo = sqldb.getDB({'valname': valname})
        try:
            mmrdata = val.mmr(dbinfo)
        except:
            embed = discord.Embed(description=(valname.capitalize()+ " has not played a competitive game this season"))
            await channel.send(embed=embed)
            return
        dec = Decimal(10) ** -2
        mmrtotal = mmrdata['wins'] + mmrdata['losses']
        mmrperc = (mmrdata['wins'] / mmrtotal * 100)
        mmrperc = Decimal(mmrperc).quantize(dec)
        mmrperc = str(mmrperc) + '%'

        # streak and last 10 games
        l10 = str(mmrdata['history10']['wins']) + '-' + str(mmrdata['history10']['losses'])
        streak = mmrdata['history10']['streaktype'] + str(mmrdata['history10']['streak'])

        embed = discord.Embed(title=(valname.capitalize() + "'s Current Valorant Rank"))
        embed.add_field(name='Rank', value=mmrdata['rank'])
        embed.add_field(name='Elo In Rank', value=mmrdata['elo'], inline=False)
        embed.add_field(name='Global Rank', value=mmrdata['globalRank'], inline=False)
        embed.add_field(name='Net Elo From Last Game Played', value=mmrdata['lastGame'])
        embed.add_field(name='Wins', value=mmrdata['wins'], inline=False)
        embed.add_field(name='Losses', value=mmrdata['losses'])
        embed.add_field(name='Win Percentage', value=mmrperc,inline=False)
        embed.add_field(name='Record In Last 10 Games', value=l10, inline=False)
        embed.add_field(name='Current Streak', value=streak, inline=False)

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
        embed = discord.Embed(description=( + "This is not a valid Act"))
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
            embed = discord.Embed(description=(valname + " is not registered in the database"))
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


@client.command()
async def crosshair(ctx):

    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    valname = re.sub(r'(^.crosshair)', '', message).lstrip()

    if not (sqldb.checkDB({'valname': valname})):
        embed = discord.Embed(description=(valname.capitalize()+ " is not registered in the database"))
        await channel.send(embed=embed)
        return
    else:
        dbinfo = sqldb.getDB({'valname': valname})
        xhair = val.getXhair(dbinfo)
        clr = xhair['color']
        xcolour = discord.colour.Color.from_rgb(clr['r'], clr['g'], clr['b'])

        inner = "Thickness:" + xhair['inner']['thickness'] + '\n' + "Length:" + xhair['inner']['length'] + '\n' + "Offset:" + xhair['inner']['offset'] + '\n' + "Opacity:" + xhair['inner']['opacity'] + '\n' + xhair['inner']['showLines'] + '\n'
        outer = "Thickness:" + xhair['outer']['thickness'] + '\n' + "Length:" + xhair['outer']['length'] + '\n' + "Offset:" + xhair['outer']['offset'] + '\n' + "Opacity:" + xhair['outer']['opacity'] + '\n'+ xhair['outer']['showLines'] + '\n'

        embed = discord.Embed(title=(valname.capitalize() + "'s Crosshair"), color=xcolour)
        embed.add_field(name='Additional info', value='<---- Crosshair color\n\n', inline=False)
        embed.add_field(name='Inner Lines', value=inner, inline=False)
        embed.add_field(name='Outer Lines', value=outer, inline=False)
        embed.add_field(name='Mouse Sensitivity', value=xhair['sens'], inline=False)
        await channel.send(embed=embed)


@client.command()
async def smurfing(ctx):

    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    valnames = re.sub(r'(^.smurfing)', '', message).lstrip()
    test = valnames.find(',')
    if(valnames.find(',') == -1):
        embed = discord.Embed(description=("Please use the following format (include comma):\n .smurfing fromUser, toUser"))
        await channel.send(embed=embed)
        return

    valnames = valnames.split(',')
    getUser = valnames[0].lstrip()
    setUser = valnames[1].lstrip()

    if not (sqldb.checkDB({'valname': getUser})):
        embed = discord.Embed(description=(getUser.capitalize()+ " is not registered in the database"))
        await channel.send(embed=embed)
        return

    if not (sqldb.checkDB({'valname': setUser})):
        embed = discord.Embed(description=(setUser.capitalize()+ " is not registered in the database"))
        await channel.send(embed=embed)
        return
    else:
        dataGetUser = sqldb.getDB({'valname': getUser})
        dataSetUser = sqldb.getDB({'valname': setUser})
        val.transferSettings(dataGetUser,dataSetUser)
        embed = discord.Embed(description=(getUser.capitalize() + "'s settings have been transfered to " + setUser.capitalize()) + "'s account.\n Happy Smurfing :)")
        await channel.send(embed=embed)
        return


@client.command()
async def matchRanks(ctx):
    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    valname = re.sub(r'(^.matchRanks)', '', message).lstrip()

    if not (sqldb.checkDB({'valname': valname})):
        embed = discord.Embed(description=(valname.capitalize()+ " is not registered in the database"))
        await channel.send(embed=embed)
        return
    else:
        dbinfo = sqldb.getDB({'valname': valname})
        match = val.getMatch(dbinfo)
        if (match == False):
            embed = discord.Embed(description=(valname.capitalize()+ " is not currently in a match"))
            await channel.send(embed=embed)
            return

        users = val.getUsersInMatch(dbinfo,match)
        agentRanks = val.getAgentRanksInMatch(dbinfo,users)

        team1 = ''
        for player in agentRanks['Team1']:
            team1 = team1 + player + ': ' + agentRanks['Team1'].get(player).capitalize() + '\n'

        team2 = ''
        for player in agentRanks['Team2']:
            team2 = team2 + player + ': ' + agentRanks['Team2'].get(player).capitalize()  + '\n'

        embed = discord.Embed(title=("Rank list of players in " + valname.capitalize() + "'s current match"))
        embed.add_field(name='Team 1', value=team1, inline=False)
        embed.add_field(name='Team 2', value=team2, inline=False)
        await channel.send(embed=embed)


@client.command()
async def play(ctx, *, query):
    # check to see if user in channel
    textChannel = ctx.channel
    try:
        voiceChannel = ctx.author.voice.channel
    except:
        embed = discord.Embed(description=("You must be in a voice channel to play a song."))
        await textChannel.send(embed=embed)
        return

    message = ctx.message.content
    song = re.sub(r'(^.play)', '', message).lstrip()
    video, source = music.search(song)
    url = video['webpage_url']
    urltitle = video['title']
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    try:
        await music.add(ctx, voice, source, client, url, urltitle)
    except Exception as e:
         print(traceback.format_exc())


@client.command()
async def skip(ctx):

    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    await music.skip(ctx, voice, client)


@client.command()
async def stop(ctx):

    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    await music.stop(ctx, voice, client)

client.run('ODM4MTAzNjY5MzcwNjUwNzE1.YI2O3Q.Tuq8ZqrLshUVxyw0Qc2p6_nu-A4')
