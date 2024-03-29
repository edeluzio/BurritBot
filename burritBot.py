from decimal import Decimal
from datetime import datetime
import sqlite3
from discord.ext import commands
from bs4 import BeautifulSoup
import requests, pytz, discord, re, json, random, time, sqldb, asyncio, valBurrit, music, traceback, os

intents = discord.Intents().all()
client = commands.Bot(command_prefix='.', intents=intents)
poll = []


def check(author):
    def inner_check(message):
        return message.author == author
    return inner_check


def is_me(m):
    return m.author == client.user

def debugString(debugText):
    if os.getenv('BURRIT_DEBUG'):
        debug_text = f"{debugText}"
    else:
        debug_text = ""
    return debug_text

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

@client.event
async def on_voice_state_update(member, before, after):
    if (member.bot):
        return

    # joining channel
    if before.channel is None and after.channel is not None:
        joinTime = time.time()
        sqldb.updateLastJoined(member.id, joinTime)

    # leaving channel
    elif before.channel is not None and after.channel is None:
        leftTime = time.time()
        sqldb.updateLastLeft(member.id, leftTime)

        # update db to get total time
        sqldb.updateTotalTime(member.id)

########################################################   GENERAL COMMANDS   ################################################################################
@client.command()
async def usersignup(ctx):
    author = ctx.author
    channel = ctx.channel
    message = ctx.message

    await author.send(
        "Welcome to the Burrit user database signup.\n")

    await author.send("Respond with your username. This can be whatever you choose, and is more like a nickname")
    try:
        username = await client.wait_for('message', check=check(author), timeout=30.0)
        username = username.content
    except asyncio.TimeoutError:
        return await author.send("Sorry, you took too long too respond. Please reenter .usersignup")

    data = {'username': username, 'discordId': author.id,}
    if sqldb.checkInUsers(data['username']):
        return await author.send("This user has already signed up in the database")

    else:
        sqldb.addUser(data)
        return await author.send("You are now registered in the user database!")

@client.command()
async def removeUser(ctx):
    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    username = re.sub(r'(^.removeUser)', '', message).lstrip()

    if sqldb.checkNameInUsers(username) is False:
         return await channel.send(f"{username} is not currently registered in the database!. Use command .users to see the database")
    else:
        sqldb.delUser(username)
        return await channel.send(f"{username} succesfully deleted from the database!")

@client.command()
async def users(ctx):
    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content

    embed = discord.Embed(title='Users Currently Registered')
    embed.add_field(name='Database username', value=sqldb.getAllUsers())
    await channel.send(embed=embed)

@client.command()
async def userVoiceTimes(ctx):
    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content

    embed = discord.Embed(title='Users Currently Registered')
    embed.add_field(name='Database username', value=sqldb.getAllUserTimes())
    await channel.send(embed=embed)

@client.command()
async def burhelp(ctx):
    user = ctx.author
    await user.create_dm()

##########################################################   MOVIE COMMANDS   ################################################################################
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

############################################################   VAL COMMANDS   ################################################################################
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
        "Next, respond with your Valorant password.\n Please keep in mind that I am not currently storing passwords safely, so it is recommended to not use your usual password. You are also free to delete these messages after responding with your password")
    try:
        password = await client.wait_for('message', check=check(author), timeout=30.0)
        password = password.content
    except asyncio.TimeoutError:
        return await author.send("Sorry, you took too long too respond. Please reenter .valsignup")

    # check if val acc/ get val auth stuff. if vauth is a string, then its an error code (as on may 2022), and responses are handled inside auth
    vauth = await valBurrit.floxayAuth(username, password, author, client)

    # check db
    data = {'username': username, 'valname': valname, 'password': password, 'authdata': vauth}
    if sqldb.checkInValUsers(data):
        errmsg = "This user has already signed up in the database"
        await author.send(errmsg)
        return

    # add to db
    else:
        sqldb.addValUser(data)

        # say congrats
        return await author.send("You are now registered in the database!")

@client.command()
async def removeValUser(ctx):
    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    user = re.sub(r'(^.removeValUser)', '', message).lstrip()

    if sqldb.checkNameInValUsers(user) is False:
         return await channel.send(f"{user} is not currently registered in the database!. Use command .users to see the database")
    else:
        sqldb.delValUser(user)
        return await channel.send(f"{user} succesfully deleted from the database!")

@client.command()
async def valUsers(ctx):
    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content

    embed = discord.Embed(title='Users Currently Registered')
    embed.add_field(name='Database ID', value=sqldb.getAllValUsers())
    await channel.send(embed=embed)

async def getCode(author, session, client):
    await author.send("You just used a burrit command: Check your email for your 2FA code, and respond with this code")
    code = await client.wait_for('message', check=check(author), timeout=60.0)
    await author.send('Code recieved')
    return code.content

@client.command()
async def shop(ctx):
    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    valname = re.sub(r'(^.shop)', '', message).lstrip()

    if not sqldb.checkInValUsers({'valname': valname}):
        embed = discord.Embed(description=(f"{valname.capitalize()} is not registered in the database"))
        await channel.send(embed=embed)
    else:
        dbinfo = sqldb.getValUser({'valname': valname}, author, client)
        vshop = await valBurrit.fetchStore(dbinfo)
        if vshop is None:
            return

    fitems = ''
    for item in vshop['featured']:
        fitems += f"{item['name']}\t\t ---- {item['price']} VP\n"

    nitems = ''
    for item in vshop['normal']:
        nitems += f"{item['name']}\t\t ---- {item['price']} VP\n"

    bitems = None
    if ('bonus' in vshop):
        bitems = ''
        for item in vshop['bonus']:
            bitems += f"{item['name']}\t\t ---- {item['price']} VP\n"

    # send message back
    embed_title = valname.capitalize() + "'s Valorant Store" + debugString('(DEBUG)')
    embed = discord.Embed(title=embed_title)
    embed.add_field(name='Featured Shop', value=fitems or "Weekly shop currently has no guns (they got some weird ass shop rn)", inline=False)
    embed.add_field(name='Regular Shop', value=nitems or "Daily shop currently has no guns (they got some weird ass shop rn)", inline=False)
    embed.add_field(name='Night Shop', value=bitems or "You currently have no Night Shop", inline=False)
    await channel.send(embed=embed)

@client.command()
async def rank(ctx):

    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    valname = re.sub(r'(^.rank)', '', message).lstrip()

    if not sqldb.checkInValUsers({'valname': valname}):
        embed = discord.Embed(description=f"{valname.capitalize()} is not registered in the database")
    else:
        dbinfo = sqldb.getValUser({'valname': valname}, author, client)
        mmrdata = await valBurrit.mmr(dbinfo)

        if mmrdata is False:
            embed = discord.Embed(description=f"{valname.capitalize()} has not played a competitive game this season")
        else:
            dec = Decimal(10) ** -2
            mmrtotal = mmrdata['wins'] + mmrdata['losses']
            mmrperc = Decimal(mmrdata['wins'] / mmrtotal * 100).quantize(dec)
            mmrperc = f"{mmrperc}%"

            l10 = f"{mmrdata['history10']['wins']}-{mmrdata['history10']['losses']}-{mmrdata['history10']['ties']}"
            streak = f"{mmrdata['history10']['streaktype']}{mmrdata['history10']['streak']}"

            embed_title = valname.capitalize() + "'s Current Valorant Rank" + debugString('(DEBUG)')
            embed = discord.Embed(title=embed_title)
            embed.add_field(name='Rank', value=mmrdata['rank'])
            embed.add_field(name='Elo In Rank', value=mmrdata['elo'], inline=False)
            embed.add_field(name='Global Rank', value=mmrdata['globalRank'], inline=False)
            embed.add_field(name='Net Elo From Last Game Played', value=mmrdata['lastGame'])
            embed.add_field(name='Wins', value=mmrdata['wins'], inline=False)
            embed.add_field(name='Losses', value=mmrdata['losses'])
            embed.add_field(name='Win Percentage', value=mmrperc, inline=False)
            embed.add_field(name='Record In Last 10 Games', value=l10, inline=False)
            embed.add_field(name='Current Streak', value=streak, inline=False)

    await channel.send(embed=embed)

@client.command()
async def lastmatch(ctx):
    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    valname = re.sub(r'(^.lastmatch)', '', message).lstrip()

    if not (sqldb.checkInValUsers({'valname': valname})):
        embed = discord.Embed(description=(valname.capitalize() + " is not registered in the database"))
        await channel.send(embed=embed)
        return
    else:
        dbinfo = sqldb.getValUser({'valname': valname}, author, client)
        lastmatch = await valBurrit.lastMatch(dbinfo)
        # try:
        #     lastmatch = val.lastMatch(dbinfo)
        # except:
        #     embed = discord.Embed(description=(valname.capitalize() + " has not played a competitive game this season"))
        #     await channel.send(embed=embed)
        #     return

        embed = discord.Embed(title=(valname.capitalize() + "'s Last Competitive Game"))
        embed.add_field(name='Score', value=lastmatch['score'], inline=False)
        embed.add_field(name='Kills', value=lastmatch['kills'], inline=False)
        embed.add_field(name='Deaths', value=lastmatch['deaths'], inline=False)
        embed.add_field(name='Assists', value=lastmatch['assists'], inline=False)
        embed.add_field(name='Damage', value=lastmatch['damage'], inline=False)
        embed.add_field(name='Result', value=lastmatch['result'], inline=False)
        embed.add_field(name='Elo Gain/Loss', value=lastmatch['elo'], inline=False)
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
        if not (sqldb.checkInValUsers({'valname': valname})):
            embed = discord.Embed(description=(valname + " is not registered in the database"))
            await channel.send(embed=embed)
            return
        else:
            szn = seasons[index]['uuid']
            dbinfo = sqldb.getValUser({'valname': valname}, author, client)
            mmrdata = await valBurrit.pastmmr(dbinfo,szn)

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
async def crosshair(ctx):

    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    valname = re.sub(r'(^.crosshair)', '', message).lstrip()

    if not (sqldb.checkInValUsers({'valname': valname})):
        embed = discord.Embed(description=(valname.capitalize()+ " is not registered in the database"))
        await channel.send(embed=embed)
        return
    else:
        dbinfo = sqldb.getValUser({'valname': valname}, author, client)
        xhair = await valBurrit.getXhair(dbinfo)
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

    if not (sqldb.checkInValUsers({'valname': getUser})):
        embed = discord.Embed(description=(getUser.capitalize()+ " is not registered in the database"))
        await channel.send(embed=embed)
        return

    if not (sqldb.checkInValUsers({'valname': setUser})):
        embed = discord.Embed(description=(setUser.capitalize()+ " is not registered in the database"))
        await channel.send(embed=embed)
        return
    else:
        dataGetUser = sqldb.getValUser({'valname': getUser}, author, client)
        dataSetUser = sqldb.getValUser({'valname': setUser}, author, client)
        await valBurrit.transferSettings(dataGetUser,dataSetUser)
        embed = discord.Embed(description=(getUser.capitalize() + "'s settings have been transfered to " + setUser.capitalize()) + "'s account.\n Happy Smurfing :)")
        await channel.send(embed=embed)
        return

@client.command()
async def matchRanks(ctx):
    author = ctx.author
    channel = ctx.channel
    message = ctx.message.content
    valname = re.sub(r'(^.matchRanks)', '', message).lstrip()

    if not (sqldb.checkInValUsers({'valname': valname})):
        embed = discord.Embed(description=(valname.capitalize()+ " is not registered in the database"))
        await channel.send(embed=embed)
        return
    else:
        dbinfo = sqldb.getValUser({'valname': valname}, author, client)
        match = await valBurrit.getMatch(dbinfo)
        if (match == False):
            embed = discord.Embed(description=(valname.capitalize()+ " is not currently in a match"))
            await channel.send(embed=embed)
            return

        users = valBurrit.getUsersInMatch(dbinfo,match)
        agentRanks = valBurrit.getAgentRanksInMatch(dbinfo,users)

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

#####################################################   MUSIC COMMANDS   ################################################################################

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

if __name__ == '__main__':
    # unix
    try:
        token = os.environ['DISCORD_BOT_TOKEN']
    # windows, not a great way but easy enough
    except:
        file_path = 'token.txt'
        with open(file_path, 'r') as file:
            file_content = file.read()
            token = file_content.split()
            token = token[0]
    client.run(token)
