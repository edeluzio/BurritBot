#database stuff
import sqlite3

conn = sqlite3.connect('../db/user.db')
curs = conn.cursor()
# curs.execute("""CREATE TABLE users (
#                 username text,
#                 password text
#                 )""")

# curs.execute("INSERT INTO users VALUES ('test', 'password')")
# curs.execute("SELECT * FROM users WHERE lower( username)='test'")
user = 'test'
pw = 'password1'



def addDB(user,pw):

    #check valid user/pw

    #connect to DB
    conn = sqlite3.connect('../db/user.db')
    curs = conn.cursor()

    #add to
    curs.execute("INSERT INTO users VALUES (:username, :password)", {'username': user, 'password': pw})
    #close db







conn.commit()
conn.close()
