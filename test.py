import sqldb
import val
import sqldb

valname = 'starkazor'
data = {'valname': valname, 'username': valname, 'password': 'Starkaispro11!', 'authdata': val.auth('starkazor','Rackispro11!')}
data = sqldb.getDB({'valname': valname})
print(data)
# # val.fetchStore(data)
# val.mmr(data)
# val.clientinfo(data)
print()

# sqldb.dbinit()
print(sqldb.checkDB(data))
print(sqldb.checkDB({'valname': 'test'}))
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
