# database stuff
import sqlite3
import val


# conn = sqlite3.connect('../db/user.db')
# curs = conn.cursor()

# initialization of database
# curs.execute("""CREATE TABLE users (
#                 username text,
#                 entitlements text,
#                 authorization text,
#                 user_id text
#                 )""")


# curs.execute("INSERT INTO users VALUES ('test', 'password')")
# curs.execute("SELECT * FROM users WHERE lower( username)='test'")
# user = 'test'
# pw = 'password1'
#


def delDB(user,valname):
    conn = sqlite3.connect('db/user.db')
    curs = conn.cursor()
    curs.execute("DELETE FROM users WHERE username=:username AND valname=:valname" , {'username': user, 'valname': valname,})
    conn.commit()
    conn.close()


def dbinit():
    conn = sqlite3.connect('db/user.db')
    curs = conn.cursor()

    curs.execute("""CREATE TABLE users (
                    username text,
                    valname text,
                    password text,
                    entitlements text,
                    authorization text,
                    user_id text
                    )""")


def getAll():
    conn = sqlite3.connect('db/user.db')
    curs = conn.cursor()

    curs.execute("SELECT * FROM users")
    check = curs.fetchall()

    userlist = ''
    for users in check:
        userlist = userlist + users[1] + '\n'


    return userlist

def checkDB(data):
    # connect to DB
    conn = sqlite3.connect('db/user.db')
    curs = conn.cursor()

    valname = data['valname']

    # check if in db
    curs.execute("SELECT * FROM users WHERE valname=:valname COLLATE NOCASE", {'valname': valname})
    check = curs.fetchall()

    if check.__len__() == 0:
        return False
    else:
        return True


def addDB(data):
    # connect to DB
    conn = sqlite3.connect('db/user.db')
    curs = conn.cursor()

    valname = data['valname']
    username = data['username']
    password = data['password']
    entitlements = data['authdata']['headers']['X-Riot-Entitlements-JWT']
    authorization = data['authdata']['headers']['Authorization']
    user_id = data['authdata']['user_id']

    # add to db
    curs.execute("INSERT INTO users VALUES (:username, :valname, :password, :entitlements, :authorization, :user_id)",
                 {'username': username, 'valname': valname, 'entitlements': entitlements, 'authorization': authorization,
                  'user_id': user_id, 'password': password})

    # close db
    conn.commit()
    conn.close()


def getDB(data):
    # connect to DB
    conn = sqlite3.connect('db/user.db')
    curs = conn.cursor()

    if not (checkDB(data)):
        return False

    # get data and return in dictionary
    valname = data['valname']
    check = curs.execute("SELECT * FROM users WHERE valname=:valname COLLATE NOCASE", {'valname': valname})
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
        'password': check[0][2]
    }
    return userdata
