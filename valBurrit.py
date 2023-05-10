import asyncio
import json
import re
import requests
import socket
from collections import OrderedDict
from base64 import b64encode, b64decode
import zlib
import datetime
import sys
import riot_auth

userAgent = "RiotClient/63.0.9.4909983.4789131 %s (Windows;10;;Professional, x64)"

# auth stuff
async def floxayAuth(username, password, author, client):
    # region asyncio.run() bug workaround for Windows, remove below 3.8 and above 3.10.6
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # endregion

    session = requests.session()
    r = session.get(f'https://valorant-api.com/v1/version')
    res = r.json()

    userAgent = "RiotClient/" + res['data']['riotClientBuild'] + " %s (Windows;10;;Professional, x64)"

    CREDS = username, password, author, client
    auth = riot_auth.RiotAuth()
    auth.RIOT_CLIENT_USER_AGENT = userAgent
    await auth.authorize(*CREDS)

    # Reauth using cookies. Returns a bool indicating whether the reauth attempt was successful.
    await auth.reauthorize()

    userid = auth.user_id
    headers= {
        'Accept-Encoding': 'gzip, deflate, br',
        'User-Agent': auth.RIOT_CLIENT_USER_AGENT,
        'Authorization': f'Bearer {auth.access_token}',
        'X-Riot-Entitlements-JWT': auth.entitlements_token
    }

    return [userid, headers]


async def auth(username, password, author, client):
    answers = socket.getaddrinfo('auth.riotgames.com', 443)
    (family, type, proto, canonname, (address, port)) = answers[0]

    headers = OrderedDict({
        'Accept-Encoding': 'gzip, deflate, br',
        'Host': "auth.riotgames.com",
        'User-Agent': userAgent,
    })

    session = requests.session()
    session.headers = headers

    data = {
        'client_id': 'play-valorant-web-prod',
        'nonce': '1',
        'redirect_uri': 'https://playvalorant.com/opt_in',
        'response_type': 'token id_token',
    }
    r = session.post(f'https://{address}/api/v1/authorization', json=data, headers=headers, verify=False)

    data = {
        'type': 'auth',
        'username': username,
        'password': password
    }
    r = session.put(f'https://{address}/api/v1/authorization', json=data, headers=headers, verify=False)
    res = r.json()

    if 'error' in res:
        await author.send(f"The user {username} and password is not associated with a Riot account. Please reenter .valsignup")
        return 'userPassError'

    elif res['type'] == 'multifactor':
        import burritBot
        r = asyncio.ensure_future(burritBot.getCode(author, session, client))
        await r
        r = r.result()
        if r is False:
            return '2faCodeError'

    pattern = re.compile('access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)')
    data = pattern.findall(r.json()['response']['parameters']['uri'])[0]
    access_token = data[0]
    # print('Access Token: ' + access_token)

    headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'Host': "entitlements.auth.riotgames.com",
        'User-Agent': userAgent,
        'Authorization': f'Bearer {access_token}',
    }
    r = session.post('https://entitlements.auth.riotgames.com/api/token/v1', headers=headers, json={})
    entitlements_token = r.json()['entitlements_token']
    # print('Entitlements Token: ' + entitlements_token)

    headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'Host': "auth.riotgames.com",
        'User-Agent': userAgent,
        'Authorization': f'Bearer {access_token}',
    }

    r = session.post('https://auth.riotgames.com/userinfo', headers=headers, json={})
    user_id = r.json()['sub']
    # print('User ID: ' + user_id)
    headers['X-Riot-Entitlements-JWT'] = entitlements_token
    del headers['Host']
    session.close()

    return {
        'user_id': user_id,
        'headers': headers,
    }

def auth2fa(username, password):
    answers = socket.getaddrinfo('auth.riotgames.com', 443)
    (family, type, proto, canonname, (address, port)) = answers[0]
    headers = OrderedDict({
        'Accept-Encoding': 'gzip, deflate, br',
        'Host': "auth.riotgames.com",
        'User-Agent': userAgent
    })
    session = requests.session()
    session.headers = headers

    data = {
        'client_id': 'play-valorant-web-prod',
        'nonce': '1',
        'redirect_uri': 'https://playvalorant.com/opt_in',
        'response_type': 'token id_token',
    }
    r = session.post(f'https://{address}/api/v1/authorization', json=data, headers=headers, verify=False)

    data = {
        'type': 'auth',
        'username': username,
        'password': password
    }
    r = session.put(f'https://{address}/api/v1/authorization', json=data, headers=headers, verify=False)
    res = r.json()

    ############## 2fa stuff here #################
    return [
        session,
        res,
    ]

def auth2facode(author, client, code, session):
    answers = socket.getaddrinfo('auth.riotgames.com', 443)
    (family, type, proto, canonname, (address, port)) = answers[0]

    headers = session.headers

    data = {
        'type': 'multifactor',
        'code': code,
        'rememberDevice': False
    }
    r = session.put(f'https://{address}/api/v1/authorization', json=data, headers=headers, verify=False)

    pattern = re.compile('access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)')
    data = pattern.findall(r.json()['response']['parameters']['uri'])[0]
    access_token = data[0]

    headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'Host': "entitlements.auth.riotgames.com",
        'User-Agent': userAgent,
        'Authorization': f'Bearer {access_token}',
    }
    r = session.post('https://entitlements.auth.riotgames.com/api/token/v1', headers=headers, json={})
    entitlements_token = r.json()['entitlements_token']
    # print('Entitlements Token: ' + entitlements_token)

    headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'Host': "auth.riotgames.com",
        'User-Agent': userAgent,
        'Authorization': f'Bearer {access_token}',
    }

    r = session.post('https://auth.riotgames.com/userinfo', headers=headers, json={})
    user_id = r.json()['sub']
    # print('User ID: ' + user_id)
    headers['X-Riot-Entitlements-JWT'] = entitlements_token
    del headers['Host']
    session.close()

    return {
        'user_id': user_id,
        'headers': headers,
    }


async def clientinfo(authHeaders):
    # get client version
    r = requests.get(f'https://valorant-api.com/v1/version', headers=authHeaders)
    version = r.json()
    num = version['data']['version']
    fnum = ''
    for element in num:
        if element == '.':
            fnum = ''
        else:
            fnum = fnum + element
    cvers = version['data']['branch'] + '-shipping-' + version['data']['buildVersion'] + '-' + fnum

    client = {
        'X-Riot-ClientPlatform': "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9",
        'X-Riot-ClientVersion': cvers,
              }
    return client

# val user stuff
async def fetchStore(userdata):
    userid, headers = await floxayAuth(userdata['username'], userdata['password'], userdata['author'], userdata['client'])

    if userid is None:
        return

    # Store Request
    r = requests.get(f'https://pd.na.a.pvp.net/store/v2/storefront/' + userid, headers=headers)
    store = r.json()

    cvers = await clientinfo(headers)
    headers.update(cvers)

    # Content Request
    r = requests.get(f'https://valorant-api.com/v1/weapons/skinchromas', headers=headers)
    data = r.json()

    featuredlength = store['FeaturedBundle']['Bundle']['Items'].__len__()
    normallength = store['SkinsPanelLayout']['SingleItemOffers'].__len__()

    # try to get a the night shop since it's not always there
    try:
        bonuslength = store['BonusStore']['BonusStoreOffers'].__len__()
    except:
        pass

    fskins = []
    nskins = []
    bskins = []
    fnames = []
    nnames = []
    bnames = []
    fprices = []
    nprices = []
    bprices = []

    #get daily shop prices
    r = requests.get('https://pd.na.a.pvp.net/store/v1/offers/', headers=headers)
    dailyprice = r.json()

    # get the asset pack
    r = requests.get(f'https://valorant-api.com/v1/weapons', headers=headers)
    assets = r.json()

    # get featured store ids and names
    for i in range(featuredlength):
        fskins.append(store['FeaturedBundle']['Bundle']['Items'][i]['Item']['ItemID'])
        if (int(store['FeaturedBundle']['Bundle']['Items'][i]['BasePrice']) > 700):
            fprices.append(store['FeaturedBundle']['Bundle']['Items'][i]['BasePrice'])
    for featSkin in range(fskins.__len__()):
        for asset in range(assets['data'].__len__()):
            for skin in range(assets['data'][asset]['skins'].__len__()):
                if fskins[featSkin].lower() == assets['data'][asset]['skins'][skin]['levels'][0]['uuid'].lower():
                    fnames.append(assets['data'][asset]['skins'][skin]['levels'][0]['displayName'])

    # get normal store ids and names
    for k in range(normallength):
        nskins.append(store['SkinsPanelLayout']['SingleItemOffers'][k])
    for normSkin in range(nskins.__len__()):
        for asset in range(assets['data'].__len__()):
            for skin in range(assets['data'][asset]['skins'].__len__()):
                if nskins[normSkin].lower() == assets['data'][asset]['skins'][skin]['levels'][0]['uuid'].lower():
                    nnames.append(assets['data'][asset]['skins'][skin]['levels'][0]['displayName'])

    # try to get bonus ids and names
    try:
        for m in range(bonuslength):
            bskins.append(store['BonusStore']['BonusStoreOffers'][m]['Offer']['OfferID'])
            bprices.append(list(store['BonusStore']['BonusStoreOffers'][m]['DiscountCosts'].values())[0])
        for bonSkin in range(bskins.__len__()):
            for asset in range(assets['data'].__len__()):
                for skin in range(assets['data'][asset]['skins'].__len__()):
                    if bskins[bonSkin].lower() == assets['data'][asset]['skins'][skin]['levels'][0]['uuid'].lower():
                        bnames.append(assets['data'][asset]['skins'][skin]['levels'][0]['displayName'])
    except:
        pass

    for j in nskins:
        for i in dailyprice['Offers']:
            if i['OfferID'] == j:
                nprices.append(list(i['Cost'].values())[0])

    # # get skin images
    # fskinimages = []
    # nskinimages = []
    # bskinimages = []
    #
    # # For each gun in skinlist
    # for a in range(fskins.__len__()):
    #     # compare with each gun type
    #     for b in range(assets['data'].__len__()):
    #         # compare with each skin of that gun
    #         for c in range(assets['data'][b]['skins'].__len__()):
    #             # if the gun ids match, append the link to the list
    #             if fskins[a].lower() == assets['data'][b]['skins'][c]['levels'][0]['uuid']:
    #                 fskinimages.append(assets['data'][b]['skins'][c]['chromas'][0]['fullRender'])
    #
    # for a in range(nskins.__len__()):
    #     # compare with each gun type
    #     for b in range(assets['data'].__len__()):
    #         # compare with each skin of that gun
    #         for c in range(assets['data'][b]['skins'].__len__()):
    #             # if the gun ids match, append the link to the list
    #             if nskins[a].lower() == assets['data'][b]['skins'][c]['levels'][0]['uuid']:
    #                 nskinimages.append(assets['data'][b]['skins'][c]['chromas'][0]['fullRender'])
    #
    # for a in range(bskins.__len__()):
    #     # compare with each gun type
    #     for b in range(assets['data'].__len__()):
    #         # compare with each skin of that gun
    #         for c in range(assets['data'][b]['skins'].__len__()):
    #             # if the gun ids match, append the link to the list
    #             if bskins[a].lower() == assets['data'][b]['skins'][c]['levels'][0]['uuid']:
    #                 bskinimages.append(assets['data'][b]['skins'][c]['chromas'][0]['fullRender'])

    skinsdata = {}

    feat = {}
    norm = {}
    bon = {}

    # append prices
    feat['prices'] = fprices
    norm['prices'] = nprices
    bon['prices'] = bprices

    # append weapon images
    # feat['images'] = fskinimages
    # norm['images'] = nskinimages
    # bon['images'] = bskinimages

    # append weapon names
    feat['names'] = fnames
    norm['names'] = nnames
    bon['names'] = bnames

    # append timers
    feat['timer'] = store['FeaturedBundle']['BundleRemainingDurationInSeconds']
    norm['timer'] = store['SkinsPanelLayout']['SingleItemOffersRemainingDurationInSeconds']

    # append everything to skin data
    skinsdata['feat'] = feat
    skinsdata['norm'] = norm
    if not (bnames.__len__() == 0):
        skinsdata['bon'] = bon

    return skinsdata

def getLatestSzn():
    response = requests.get("https://valorant-api.com/v1/seasons")
    r=response.json()
    curDate = datetime.datetime.today()
    for season in r["data"]:
        if season["type"] is None:
            actName = season["displayName"].replace(" ", "")
        else:
            sznStart = datetime.datetime.strptime(season["startTime"][0:10], "%Y-%m-%d")
            sznEnd = datetime.datetime.strptime(season["endTime"][0:10], "%Y-%m-%d")
            if sznStart <= curDate <= sznEnd:
                uuid = season["uuid"]
                break
    return {
        "uuid": uuid,
        "actName": actName
    }

async def mmr(userdata):
    userid, headers = await floxayAuth(userdata['username'], userdata['password'], userdata['author'], userdata['client'])

    if userid is False:
        return

    cvers = await clientinfo(headers)
    headers.update(cvers)
    url = 'https://pd.na.a.pvp.net/mmr/v1/players/' + userid
    r = requests.get(url, headers=headers)
    rating = r.json()

    seasonInfo = getLatestSzn()
    try:
        sznrating = rating['QueueSkills']['competitive']['SeasonalInfoBySeasonID'][seasonInfo["uuid"]]
    except:
        return False

    if sznrating['LeaderboardRank'] == 0:
        globalRank = "Too shit to be on leaderboard"
    else:
        globalRank = str(sznrating['LeaderboardRank'])

    mmrdata = {
        'ranknum': sznrating['CompetitiveTier'],
        'elo': sznrating['RankedRating'],
        'wins': sznrating['NumberOfWins'],
        'losses': sznrating['NumberOfGames'] - sznrating['NumberOfWins'],
        'lastGame': rating['LatestCompetitiveUpdate']['RankedRatingEarned'],
        'globalRank': globalRank,
    }

    r = requests.get('https://valorant-api.com/v1/competitivetiers')
    tiers = r.json()

    for episode in tiers['data']:
        if episode["assetObjectName"].split("_")[0].lower() == seasonInfo["actName"].lower():
            for ranks in episode["tiers"]:
                if mmrdata['ranknum'] == ranks['tier']:
                    mmrdata['rank'] = ranks['tierName']
                    break

    url = "https://pd.na.a.pvp.net/mmr/v1/players/" + userid + "/competitiveupdates?startIndex=0&queue=competitive"
    r = requests.get(url, headers=headers)
    matches = r.json()

    # last 10 history
    games = 0
    streak = 1
    streaktype = None
    finalstreak = None
    games = 0
    wins = 0
    losses = 0
    ties = 0
    for match in matches['Matches']:
        # disregard dodges
        if match['MapID'] == '':
            continue
        # get game info
        url = "https://pd.na.a.pvp.net/match-details/v1/matches/" + match['MatchID']
        r = requests.get(url, headers=headers)
        gameinfo = r.json()
        # check make sure its ranked game
        # get player team
        for player in gameinfo['players']:
            if player['subject'].lower() == userid.lower():
                pteam = player['teamId']
                break
        # check if win or loss
        for team in gameinfo['teams']:
            if team['teamId'] == pteam:
                games = games + 1

                if pteam == gameinfo['teams'][0]['teamId']:
                    otherTeam = gameinfo['teams'][1]
                else:
                    otherTeam = gameinfo['teams'][0]

                # set streak type
                if games == 1:
                    if team['won'] is True and otherTeam['won'] is False:
                        streaktype = 'W'
                    elif team['won'] is False and otherTeam['won'] is False:
                        streaktype = 'T'
                    else:
                        streaktype = 'L'

                elif team['won'] is True and otherTeam['won'] is False:
                    wins = wins + 1
                    if streaktype == 'W' and finalstreak is None:
                        streak = streak + 1
                    else:
                        finalstreak = streak

                elif team['won'] is False and otherTeam['won'] is False:
                    ties = ties + 1
                    if streaktype == 'T' and finalstreak is None:
                        streak = streak + 1
                    else:
                        finalstreak = streak

                else:
                    losses = losses + 1
                    if streaktype == 'L' and finalstreak is None:
                        streak = streak + 1
                    else:
                        finalstreak = streak

        # stop at 10 games
        if games == 10:
            break

    history10 = {
        'wins': wins,
        'losses': losses,
        'ties': ties,
        'streak': finalstreak,
        'streaktype': streaktype,
    }
    mmrdata['history10'] = history10
    return mmrdata

async def lastMatch(userdata):
    userid, headers = await floxayAuth(userdata['username'], userdata['password'], userdata['author'], userdata['client'])

    if userid is False:
        return
    cvers = await clientinfo(headers)
    headers.update(cvers)

    url = "https://pd.na.a.pvp.net/mmr/v1/players/" + userid + "/competitiveupdates?startIndex=0&endIndex=1&queue=competitive"
    r = requests.get(url, headers=headers)
    matches = r.json()
    game = matches['Matches'][0]['MatchID']

    url = "https://pd.na.a.pvp.net/match-details/v1/matches/" + game
    r = requests.get(url, headers=headers)
    gameinfo = r.json()

    matchData = {}
    for player in gameinfo['players']:
        if player['subject'].lower() == userid.lower():
            # get player info
            team = player['teamId']

            # get damage
            damage = 0
            for damageValues in player['roundDamage']:
                damage = damage + damageValues['damage']

            for teams in gameinfo['teams']:
                if teams['teamId'] == team:
                    if teams['won'] is True:
                        result = 'Win'
                    else:
                        result = 'Loss'

            matchData['score'] = player['stats']['score']
            matchData['kills'] = player['stats']['kills']
            matchData['deaths'] = player['stats']['deaths']
            matchData['assists'] = player['stats']['assists']
            matchData['damage'] = damage
            matchData['result'] = result
            matchData['elo'] = matches['Matches'][0]['RankedRatingEarned']

            return matchData


async def pastmmr(userdata,szn):
    userid, headers = await floxayAuth(userdata['username'], userdata['password'], userdata['author'], userdata['client'])
    if userid is False:
        return
    cvers = await clientinfo(headers)
    headers.update(cvers)
    url = 'https://pd.na.a.pvp.net/mmr/v1/players/' + userid

    r = requests.get(url, headers=headers)
    seasons = r.json()

    past = seasons['QueueSkills']['competitive']['SeasonalInfoBySeasonID'][szn]

    mmrdata = {
        'ranknum': past['CompetitiveTier'],
        'sznrank': past['Rank'],
        'wins': past['NumberOfWins'],
        'losses': past['NumberOfGames'] - past['NumberOfWins'],
    }

    r = requests.get('https://valorant-api.com/v1/competitivetiers')
    tiers = r.json()

    for ranks in tiers['data'][1]['tiers']:
        if mmrdata['ranknum'] == ranks['tier']:
            mmrdata['rank'] = ranks['tierName']
        if mmrdata['sznrank'] == ranks['tier']:
            mmrdata['sznrank'] = ranks['tierName']

    return mmrdata

def getXhairNorm(settings):
    EA = 'EAresStringSettingName::'
    for index in settings['stringSettings']:
        if (index['settingEnum'] == EA + "SavedCrosshairProfileData"):
            settingsXhair = json.loads(index['value'])


    # get current crosshair profile
    currProfIndex = settingsXhair['currentProfile']
    currProf = settingsXhair['profiles'][currProfIndex]['primary']
    xhair = {}

    # get mouse sens
    EA = 'EAresFloatSettingName::'
    # get sens
    for index in settings['floatSettings']:
        if (index['settingEnum'] == EA + "MouseSensitivity"):
            xhair['sens'] = round(index['value'], 3)

    # get color
    xhair['color'] = currProf['color']

    # get inner
    inner = {}
    inner['thickness'] = str(currProf['innerLines']['lineThickness'])
    inner['length'] = str(currProf['innerLines']['lineLength'])
    inner['offset'] = str(currProf['innerLines']['lineOffset'])
    inner['opacity'] = str(currProf['innerLines']['opacity'])
    inner['showLines'] = 'Show Lines = ' + str(currProf['innerLines']['bShowLines'])
    xhair['inner'] = inner

    # get outer
    outer = {}
    outer['thickness'] = str(currProf['outerLines']['lineThickness'])
    outer['length'] = str(currProf['outerLines']['lineLength'])
    outer['offset'] = str(currProf['outerLines']['lineOffset'])
    outer['opacity'] = str(currProf['outerLines']['opacity'])
    outer['showLines'] = 'Show Lines = ' + str(currProf['outerLines']['bShowLines'])
    xhair['outer'] = outer

    return xhair

def getXhairSpec(settings):
    xhair = {}

    # get sens
    xhair['sens'] = str(round(settings['floatSettings'][0]['value'], 3))

    # get inner
    inner = {}
    inner['thickness'] = str(settings['floatSettings'][3]['value'])
    inner['length'] = str(settings['floatSettings'][4]['value'])
    inner['offset'] = str(settings['floatSettings'][5]['value'])
    inner['opacity'] = str(settings['floatSettings'][6]['value'])
    xhair['inner'] = inner

    # get outer
    outer = {}
    outer['thickness'] = str(settings['floatSettings'][7]['value'])
    outer['length'] = str(settings['floatSettings'][8]['value'])
    outer['offset'] = str(settings['floatSettings'][9]['value'])
    outer['opacity'] = str(settings['floatSettings'][10]['value'])
    xhair['outer'] = outer

    # get color
    colorog = settings['stringSettings'][2]['value']
    colorog = re.sub(r'[a-zA-z=()]', r'', colorog)
    colorog = colorog.split(',')
    color = {}
    color['r'] = int(colorog[0])
    color['g'] = int(colorog[1])
    color['b'] = int(colorog[2])
    xhair['color'] = color

    return xhair

async def getXhair(userdata):

    userid, headers = await floxayAuth(userdata['username'], userdata['password'], userdata['author'], userdata['client'])
    if userid is False:
        return

    cvers = await clientinfo(headers)
    headers.update(cvers)

    url = 'https://playerpreferences.riotgames.com/playerPref/v3/getPreference/Ares.PlayerSettings'
    r = requests.get(url, headers=headers)
    settings = r.json()
    settings = inflate_decode(settings['data'])
    settings = json.loads(settings)

    # specFlag = True
    # for index in settings['stringSettings']:
    #     if (index['settingEnum'] == 'EAresStringSettingName::CrosshairSettings'):
    #         specFlag = False
    #
    # if (specFlag == True):
    #     return getXhairSpec(settings)
    # else:
    return getXhairNorm(settings)

async def transferSettings(dataGetUser,dataSetUser):
    settings = await getSettings(dataGetUser)
    await putSettings(dataSetUser, settings)

async def getSettings(userdata):

    userid, headers = await floxayAuth(userdata['username'], userdata['password'], userdata['author'], userdata['client'])
    if userid is False:
        return

    cvers = await clientinfo(headers)
    headers.update(cvers)
    headers = headers

    url = 'https://playerpreferences.riotgames.com/playerPref/v3/getPreference/Ares.PlayerSettings'
    r = requests.get(url, headers=headers)
    response = r.json()
    return response

async def putSettings(userdata, settings):

    userid, headers = await floxayAuth(userdata['username'], userdata['password'], userdata['author'], userdata['client'])
    cvers = await clientinfo(headers)
    headers.update(cvers)
    headers = headers

    url = 'https://playerpreferences.riotgames.com/playerPref/v3/savePreference'
    r = requests.put(url,json=settings, headers=headers)

async def getMatch(userdata):
    userid, headers = await floxayAuth(userdata['username'], userdata['password'], userdata['author'], userdata['client'])
    if userid is False:
        return
    cvers = await clientinfo(headers)
    headers.update(cvers)
    url = 'https://glz-na-1.na.a.pvp.net/core-game/v1/players/' + userid

    r = requests.get(url, headers=headers)
    match = r.json()

    if not(r.status_code == 200):
        return False

    match = match['MatchID']
    return match

async def getUsersInMatch(userdata,matchID):
    userid, headers = await floxayAuth(userdata['username'], userdata['password'], userdata['author'], userdata['client'])
    if userid is False:
        return
    cvers = await clientinfo(headers)
    headers.update(cvers)
    url = 'https://glz-na-1.na.a.pvp.net/core-game/v1/matches/' + matchID

    r = requests.get(url, headers=headers)
    users = r.json()

    if not(r.status_code == 200):
        return False

    users = users['Players']
    return users

def getAgentRanksInMatch(userdata,playerlist):
    agents = getAgents(userdata)

    ranklist = {}
    team1 = {}
    team2 = {}
    for player in playerlist:
        for agent in agents:
            if (player['CharacterID'] == agent['ID'].lower()):
                if(player['TeamID'] == 'Blue'):
                    team1[agent['Name']] = player['SeasonalBadgeInfo']['Rank']
                else:
                    team2[agent['Name']] = player['SeasonalBadgeInfo']['Rank']



    # update to string ranks
    r = requests.get('https://valorant-api.com/v1/competitivetiers')
    tiers = r.json()

    for ranks in tiers['data'][1]['tiers']:
        for intRank in team1:
            if team1.get(intRank) == ranks['tier']:
                temp = {intRank: ranks['tierName']}
                team1.update(temp)

    for ranks in tiers['data'][1]['tiers']:
        for intRank in team2:
            if team2.get(intRank) == ranks['tier']:
                temp = {intRank: ranks['tierName']}
                team2.update(temp)

    ranklist = {
        'Team1': team1,
        'Team2': team2,
    }

    return ranklist

async def getAgents(userdata):
    userid, headers = await floxayAuth(userdata['username'], userdata['password'], userdata['author'], userdata['client'])
    if userid is False:
        return
    cvers = await clientinfo(headers)
    headers.update(cvers)
    # url = 'https://shared.na.a.pvp.net/content-service/v2/content'
    url = 'https://valorant-api.com/v1/agents'

    r = requests.get(url, headers=headers)
    charlist = r.json()
    return charlist

async def getPlayerLoadout(userdata):

    userid, headers = await floxayAuth(userdata['username'], userdata['password'], userdata['author'], userdata['client'])
    if userid is False:
        return
    cvers = await clientinfo(headers)
    headers.update(cvers)
    url = 'https://pd.NA.a.pvp.net/personalization/v2/players/' + userid + '/playerloadout'

    r = requests.get(url, headers=headers)
    player = r.json()
    return player

async def getPlayerWeapons(userdata):

    userid, headers = await floxayAuth(userdata['username'], userdata['password'], userdata['author'], userdata['client'])
    if userid is False:
        return
    cvers = await clientinfo(headers)
    headers.update(cvers)

    url = 'https://pd.NA.a.pvp.net/store/v1/entitlements/' + userid + '/e7c63390-eda7-46e0-bb7a-a6abdacd2433'
    r = requests.get(url, headers=headers)
    playerSkinLevels = r.json()
    playerSkinLevels = playerSkinLevels['Entitlements']

    url = 'https://pd.NA.a.pvp.net/store/v1/entitlements/' + userid + '/3ad1b2b2-acdb-4524-852f-954a76ddae0a'
    r = requests.get(url, headers=headers)
    playerSkinChromas = r.json()
    playerSkinChromas = playerSkinChromas['Entitlements']

    return {
        'playerSkinChromas': playerSkinChromas,
        'playerSkinLevels': playerSkinLevels
            }

async def getContentWeapons(userdata):

    userid, headers = await floxayAuth(userdata['username'], userdata['password'], userdata['author'], userdata['client'])
    if userid is False:
        return
    cvers = await clientinfo(headers)
    headers.update(cvers)
    r = requests.get(f'https://shared.na.a.pvp.net/content-service/v2/content', headers=headers)
    weapons = r.json()
    weapons = weapons['SkinLevels']
    return weapons

# encode/decode stuff
def inflate_decode(string: str):
    return zlib.decompress(b64decode(string), -zlib.MAX_WBITS).decode('UTF-8')

def inflate_encode (string: str):
    # b64 encoded deflated full settings
    data = b64encode(string)
    string = string.encode()
    compress = zlib.compressobj()
    data1 = compress.compress(data)
    return data

def deflate(string: bytes, compress_level: int = 9):
    compress = zlib.compressobj(
            compress_level,       # level: 0-9
            zlib.DEFLATED,        # method: must be DEFLATED
            -zlib.MAX_WBITS,      # window size in bits:
                                  #   -15..-8: negate, suppress header
                                  #   8..15: normal
                                  #   16..30: subtract 16, gzip header
            zlib.DEF_MEM_LEVEL,   # mem level: 1..8/9
            0                     # strategy:
                                  #   0 = Z_DEFAULT_STRATEGY
                                  #   1 = Z_FILTERED
                                  #   2 = Z_HUFFMAN_ONLY
                                  #   3 = Z_RLE
                                  #   4 = Z_FIXED
    )
    deflated = compress.compress(string)
    deflated += compress.flush()
    return deflated

def inflate(string: bytes):
    decompress = zlib.decompressobj(
        -zlib.MAX_WBITS  # see above
    )
    inflated = decompress.decompress(string)
    inflated += decompress.flush()
    return inflated

def decode_base64_and_inflate(string: str):
    return inflate(b64decode(string)).decode('UTF-8')

def deflate_and_base64_encode(string: str):
    return b64encode(deflate(string.encode())).decode('UTF-8')

