# database stuff
import sqlite3
import datetime


##################################################### Other DB ######################################################
def dbinit():

    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()

    curs.execute("""CREATE TABLE users (
                    username text,
                    discordId text,
                    lastJoinedVC INT DEFAULT 0,
                    lastLeftVC INT DEFAULT 0,
                    totalTimeVC INT DEFAULT 0)""")


    # curs.execute("""CREATE TABLE valUsers (
    #                 username text,
    #                 valname text,
    #                 password text,
    #                 entitlements text,
    #                 authorization text,
    #                 user_id text
    #                 )""")

##################################################### User DB ######################################################
def addUser(data):
    # connect to DB
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()

    username = data['username']
    discordId = data['discordId']

    # add to db
    curs.execute("INSERT INTO users (username, discordId) VALUES (:username, :discordId)",
                 {'username': username, 'discordId': discordId})

    # close db
    conn.commit()
    conn.close()

def delUser(username):
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()
    curs.execute("DELETE FROM users WHERE username=:username" , {'username': username})
    conn.commit()
    conn.close()

def getUser(username):
    # connect to DB
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()

    if not (checkInUsers(username)):
        return False

    # get data and return in dictionary
    check = curs.execute("SELECT * FROM users WHERE username=:username COLLATE NOCASE", {'username': username})
    check = curs.fetchall()
    userdata = {
        'username': check[0][0],
        'discordId': check[0][1],
        'lastJoinedVC': check[0][2],
        'lastLeftVC': check[0][3],
        'totalTimeVC': check[0][4],
    }

    return userdata

def getAllUsers():
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()

    curs.execute("SELECT * FROM users")
    check = curs.fetchall()

    userlist = ''
    for users in check:
        userlist = userlist + users[0] + '\n'

    return userlist

def checkNameInUsers(username):
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()
    check = curs.execute("SELECT * FROM users WHERE username=:username COLLATE NOCASE", {'username': username})
    check = curs.fetchall()
    conn.commit()
    conn.close()
    if len(check) == 0:
        return False
    return True

def checkInUsers(username):
    # connect to DB
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()

    curs.execute("SELECT * FROM users WHERE username=:username COLLATE NOCASE", {'username': username})
    check = curs.fetchall()

    if check.__len__() == 0:
        return False
    else:
        return True

def updateLastJoined(discordId, joinTime):
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()
    curs.execute("UPDATE users SET lastJoinedVC=:joinTime WHERE discordId=:discordId COLLATE NOCASE", {'joinTime': joinTime,'discordId': discordId})
    conn.commit()
    conn.close()

def updateLastLeft(discordId, leftTime):
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()
    curs.execute("UPDATE users SET lastLeftVC=:leftTime WHERE discordId=:discordId COLLATE NOCASE", {'leftTime': leftTime,'discordId': discordId})
    conn.commit()
    conn.close()

def updateTotalTime(discordId):
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()
    check = curs.execute("SELECT * FROM users WHERE discordId=:discordId COLLATE NOCASE", {'discordId': discordId})
    check = curs.fetchall()
    username = check[0][0]
    userDbInfo = getUser(username)

    if userDbInfo['lastJoinedVC'] == 0:
        return
    elapsedTime = userDbInfo['lastLeftVC'] - userDbInfo['lastJoinedVC']
    newTotalTime = userDbInfo['totalTimeVC'] + elapsedTime

    print()
    curs.execute("UPDATE users SET totalTimeVC=:newTotalTime WHERE discordId=:discordId COLLATE NOCASE", {'newTotalTime': newTotalTime,'discordId': discordId})
    conn.commit()
    conn.close()

def getAllUserTimes():
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()

    curs.execute("SELECT username, totalTimeVC FROM users")
    check = curs.fetchall()

    userlist = ''
    for users in check:
        totalTime = str(datetime.timedelta(seconds=users[1]))
        userlist = userlist + users[0] + ":     %s" % str(totalTime).split('.')[0] + '\n'

    return userlist

##################################################### Val DB ######################################################

def checkNameInValUsers(valname):
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()
    check = curs.execute("SELECT * FROM valUsers WHERE valname=:valname COLLATE NOCASE", {'valname': valname})
    check = curs.fetchall()
    conn.commit()
    conn.close()
    if len(check) == 0:
        return False
    return True

def delValUser(valname):
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()
    curs.execute("DELETE FROM valUsers WHERE valname=:valname" , {'valname': valname,})
    conn.commit()
    conn.close()

def getAllValUsers():
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()

    curs.execute("SELECT * FROM valUsers")
    check = curs.fetchall()

    userlist = ''
    for users in check:
        userlist = userlist + users[1] + '\n'


    return userlist

def checkInValUsers(data):
    # connect to DB
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()

    valname = data['valname']

    # check if in db
    curs.execute("SELECT * FROM valUsers WHERE valname=:valname COLLATE NOCASE", {'valname': valname})
    check = curs.fetchall()

    if check.__len__() == 0:
        return False
    else:
        return True

def addValUser(data):
    # connect to DB
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()

    valname = data['valname']
    username = data['username']
    password = data['password']
    entitlements = data['authdata']['headers']['X-Riot-Entitlements-JWT']
    authorization = data['authdata']['headers']['Authorization']
    user_id = data['authdata']['user_id']

    # add to db
    curs.execute("INSERT INTO valUsers VALUES (:username, :valname, :password, :entitlements, :authorization, :user_id)",
                 {'username': username, 'valname': valname, 'entitlements': entitlements, 'authorization': authorization,
                  'user_id': user_id, 'password': password})

    # close db
    conn.commit()
    conn.close()

def getValUser(data, author, client):
    # connect to DB
    conn = sqlite3.connect('db/burrit.db')
    curs = conn.cursor()

    if not (checkInValUsers(data)):
        return False

    # get data and return in dictionary
    valname = data['valname']
    check = curs.execute("SELECT * FROM valUsers WHERE valname=:valname COLLATE NOCASE", {'valname': valname})
    check = curs.fetchall()
    headers = {
        'X-Riot-Entitlements-JWT': check[0][3],
        'Authorization': check[0][4],
    }

    authdata = {
        'headers': headers,
        'user_id': check[0][5],
    }

    userdata = {
        'authdata': authdata,
        'username': check[0][0],
        'valname': valname,
        'password': check[0][2],
        'author': author,
        'client': client,
    }
    return userdata
