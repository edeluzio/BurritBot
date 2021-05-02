import discord
import re
from discord.ext import commands

client = commands.Bot(command_prefix='.')

@client.event
async def on_ready():
    print("Bot is ready")

@client.command()
async def update(ctx):
    channel = discord.utils.get(ctx.guild.channels, name="test")
    messages = await channel.history(limit=500).flatten()
    tmessages = []
    rankings = []

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
        #print(tmsg)
        match = re.match(r"([0-9\.\s]+[a-zA-Z|\s]+)([0-9|\.]+)", tmsg, re.I)
        if (match):
            title = match.groups()[0]
            result = re.sub(r'([\d]+[\.][\s])', '', title)
            title = result.rstrip()
            ranks.append(match.groups()[1])
            #print(match1.groups())

        mov = [title, ranks]
        #print(mov)

        # if movie hasnt been evaluated yet, add to list. otherwise skip it. also check for blank movie option
        inlist = False
        for i in rankings:
            if mov[0] in i[0]:
                inlist = True

        if not (inlist) and not mov[0] == '':
            rankings.append(mov)
        else:
            for i in rankings:
                if mov[0] in i[0]:
                    i[1].append(mov[1][0])

    # get average for each movie
    for film in rankings:
        avgrank = float(0)

        # get sum of ranks
        if not (film[0] == ''):
            for nums in film[1]:
                avgrank = avgrank + float(nums)

            # get average of rank
            avgrank = round (avgrank / film[1].__len__(), 2)

            # append to list
            film.append(avgrank)

        # if blank movie then just delete from list
        else:
            film.remove()

    # bot writes/edits message to server
    final = "The current rankings are:\n"
    for film in rankings:
        final = final + film[0] + ": " + str(film[2]) + "\n"

    await channel.send(final)



client.run('ODM4MTAzNjY5MzcwNjUwNzE1.YI2O3Q.Tuq8ZqrLshUVxyw0Qc2p6_nu-A4')
