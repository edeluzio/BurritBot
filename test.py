import sqldb
import val
import sqldb

username = 'starkazor'
password = 'Rackispro11!'

data = {
    'authdata': val.auth(username, password),
    'username': username,
        }

val.auth(username,password)
# sqldb.dbinit()
# print(sqldb.checkDB(data))
# sqldb.addDB(data)
# print(sqldb.checkDB(data))
# print(sqldb.getDB(data))
#
# username = 'zpolitoed'
# password = 'weinor123'
#
#
# data = {
#     'authdata': val.auth(username, password),
#     'username': username,
#         }
#
# print(sqldb.checkDB(data))
# sqldb.addDB(data)
# print(sqldb.checkDB(data))
# print(sqldb.getDB(data))
