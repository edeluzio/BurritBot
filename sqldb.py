#database stuff
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

def dbinit():
    conn = sqlite3.connect('db/user.db')
    curs = conn.cursor()

    curs.execute("""CREATE TABLE users (
                    username text,
                    entitlements text,
                    authorization text,
                    user_id text
                    )""")

def checkDB(data):
    #connect to DB
    conn = sqlite3.connect('db/user.db')
    curs = conn.cursor()

    username = data['username']

    #check if in db
    curs.execute("SELECT * FROM users WHERE username=:username", {'username': username})
    check = curs.fetchall()

    if check.__len__() == 0:
        return False
    else:
        return True


def addDB(data):
    #connect to DB
    conn = sqlite3.connect('db/user.db')
    curs = conn.cursor()

    username = data['username']
    entitlements = data['authdata']['headers']['X-Riot-Entitlements-JWT']
    authorization = data['authdata']['headers']['Authorization']
    user_id = data['authdata']['user_id']

    #add to db
    curs.execute("INSERT INTO users VALUES (:username, :entitlements, :authorization, :user_id)", {'username': username, 'entitlements': entitlements, 'authorization': authorization, 'user_id': user_id})

    #close db
    conn.commit()
    conn.close()

def getDB(data):

    #connect to DB
    conn = sqlite3.connect('db/user.db')
    curs = conn.cursor()

    if not (checkDB(data)):
        return False

    # get data and return in dictionary
    username = data['username']
    check = curs.execute("SELECT * FROM users WHERE username=:username", {'username': username})
    check = curs.fetchall()
    headers = {
        'X-Riot-Entitlements-JWT': check[0][1],
        'Authorization': check[0][2],
    }

    sqldata = {
        'headers': headers,
        'user_id': check[0][3],
    }
    return sqldata

