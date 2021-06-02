import asyncio
import json
import aiohttp
import re
import requests


def auth(username, password):
    session = requests.session()
    data = {
        'client_id': 'play-valorant-web-prod',
        'nonce': '1',
        'redirect_uri': 'https://playvalorant.com/opt_in',
        'response_type': 'token id_token',
    }
    r = session.post('https://auth.riotgames.com/api/v1/authorization', json=data)

    data = {
        'type': 'auth',
        'username': username,
        'password': password
    }
    r = session.put('https://auth.riotgames.com/api/v1/authorization', json=data)
    pattern = re.compile(
        'access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)')
    data = pattern.findall(r.json()['response']['parameters']['uri'])[0]
    access_token = data[0]

    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    r = session.post('https://entitlements.auth.riotgames.com/api/token/v1', headers=headers, json={})
    entitlements_token = r.json()['entitlements_token']

    r = session.post('https://auth.riotgames.com/userinfo', headers=headers, json={})
    user_id = r.json()['sub']

    # main program done
    # access_token
    # entitlements_token
    # user_id

    headers = {
        'X-Riot-Entitlements-JWT': entitlements_token,
        'Authorization': f'Bearer {access_token}',
    }
    authdata = {
        'headers': headers,
        'user_id': user_id
    }
    userdata = {
        'username': username,
        'authdata': authdata,
    }
    return userdata
    session.close()


def clientinfo(userdata):
    # get client version
    r = requests.get(f'https://valorant-api.com/v1/version', headers=userdata['authdata']['headers'])
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


def fetchStore(userdata):

    cvers = clientinfo(userdata)
    userdata['authdata']['headers'].update(cvers)

    # Store Request
    r = requests.get(f'https://pd.na.a.pvp.net/store/v2/storefront/' + userdata['authdata']['user_id'], headers=userdata['authdata']['headers'])
    store = r.json()

    # Content Request
    r = requests.get(f'https://shared.na.a.pvp.net/content-service/v2/content', headers=userdata['authdata']['headers'])
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

    # get featured ids, prices and append
    for i in range(featuredlength):
        fskins.append(store['FeaturedBundle']['Bundle']['Items'][i]['Item']['ItemID'])
        if (int(store['FeaturedBundle']['Bundle']['Items'][i]['BasePrice']) > 700):
            fprices.append(store['FeaturedBundle']['Bundle']['Items'][i]['BasePrice'])
    # append weapon name to a list, will be used for captions of the images
    for j in range(fskins.__len__()):
        for l in range(data['SkinLevels'].__len__()):
            if (fskins[j].lower() == data['SkinLevels'][l]['ID'].lower()):
                fnames.append(data['SkinLevels'][l]['Name'])

    # get normal ids
    for k in range(normallength):
        nskins.append(store['SkinsPanelLayout']['SingleItemOffers'][k])
        nprices.append(store['FeaturedBundle']['Bundle']['Items'][k]['BasePrice'])
    # append weapon name to list
    for j in range(nskins.__len__()):
        for l in range(data['SkinLevels'].__len__()):
            if nskins[j].lower() == data['SkinLevels'][l]['ID'].lower():
                nnames.append(data['SkinLevels'][l]['Name'])

    # try to get bonus ids and print
    try:
        for m in range(bonuslength):
            bskins.append(store['BonusStore']['BonusStoreOffers'][m]['Offer']['OfferID'])
            bprices.append(store['FeaturedBundle']['Bundle']['Items'][m]['BasePrice'])
        # append weapon name to list
        for j in range(bskins.__len__()):
            for l in range(data['SkinLevels'].__len__()):
                if (bskins[j].lower() == data['SkinLevels'][l]['ID'].lower()):
                    bnames.append(data['SkinLevels'][l]['Name'])
    except:
        pass

    # get the asset pack
    r = requests.get(f'https://valorant-api.com/v1/weapons', headers=userdata['authdata']['headers'])
    assets = r.json()

    fskinimages = []
    nskinimages = []
    bskinimages = []

    # For each gun in skinlist
    for a in range(fskins.__len__()):
        # compare with each gun type
        for b in range(assets['data'].__len__()):
            # compare with each skin of that gun
            for c in range(assets['data'][b]['skins'].__len__()):
                # if the gun ids match, append the link to the list
                if fskins[a].lower() == assets['data'][b]['skins'][c]['levels'][0]['uuid']:
                    fskinimages.append(assets['data'][b]['skins'][c]['chromas'][0]['fullRender'])

    for a in range(nskins.__len__()):
        # compare with each gun type
        for b in range(assets['data'].__len__()):
            # compare with each skin of that gun
            for c in range(assets['data'][b]['skins'].__len__()):
                # if the gun ids match, append the link to the list
                if nskins[a].lower() == assets['data'][b]['skins'][c]['levels'][0]['uuid']:
                    nskinimages.append(assets['data'][b]['skins'][c]['chromas'][0]['fullRender'])

    for a in range(bskins.__len__()):
        # compare with each gun type
        for b in range(assets['data'].__len__()):
            # compare with each skin of that gun
            for c in range(assets['data'][b]['skins'].__len__()):
                # if the gun ids match, append the link to the list
                if bskins[a].lower() == assets['data'][b]['skins'][c]['levels'][0]['uuid']:
                    bskinimages.append(assets['data'][b]['skins'][c]['chromas'][0]['fullRender'])

    skinsdata = {}

    feat = {}
    norm = {}
    bon = {}

    # append prices
    feat['prices'] = fprices
    norm['prices'] = nprices
    bon['prices'] = bprices

    # append weapon images
    feat['images'] = fskinimages
    norm['images'] = nskinimages
    bon['images'] = bskinimages

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
    if not (bon['images'].__len__() == 0):
        skinsdata['bon'] = bon

    return skinsdata

def getLatestSzn():
    response = requests.get("https://valorant-api.com/v1/seasons")
    for season in response.json()["data"]:
        uuid = season["uuid"]
    return uuid

def mmr(userdata):

    cvers = clientinfo(userdata)
    userdata['authdata']['headers'].update(cvers)
    url = 'https://pd.na.a.pvp.net/mmr/v1/players/' + userdata['authdata']['user_id']

    r = requests.get(url, headers=userdata['authdata']['headers'])
    rating = r.json()

    season = getLatestSzn()
    rating = rating['QueueSkills']['competitive']['SeasonalInfoBySeasonID'][season]

    mmrdata = {
        'ranknum': rating['Rank'],
        'elo': rating['RankedRating'],
        'wins': rating['NumberOfWins'],
        'losses': rating['NumberOfGames'] - rating['NumberOfWins']
    }


    r =requests.get('https://valorant-api.com/v1/competitivetiers')
    tiers = r.json()

    for ranks in tiers['data'][1]['tiers']:
        if mmrdata['ranknum'] == ranks['tier']:
            mmrdata['rank'] = ranks['tierName']


    print(rating)
