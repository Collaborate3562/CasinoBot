import mysql.connector

# db = mysql.connector.connect(host = "localhost",user = "root",passwd = "",database = "test1")
db = mysql.connector.connect(user='root', password='bluesky0812',host='localhost',database = 'DB_AleekkCasino', auth_plugin='mysql_native_password')
cur = db.cursor()

async def updateSetStrWhereStr(table : str, field : str, value : str, where : str, wherestr : str) -> bool:
    bRes = False
    try:
        query = f"UPDATE {table} SET {field}='{value}' WHERE {where}='{wherestr}';"
        cur.execute(query)
        db.commit()
        bRes = True
        print("Field updated sucessfully")
    except:
        bRes = False
        print("update error")
    return bRes

async def updateSetFloatWhereStr(table : str, field : str, value : float, where : str, wherestr : str) -> bool:
    bRes = False
    try:
        query = f"UPDATE {table} SET {field}={value} WHERE {where}='{wherestr}';"
        cur.execute(query)
        db.commit()
        bRes = True
        print("Field updated sucessfully")
    except:
        bRes = False
        print("update error")
    return bRes

async def readFieldsWhereStr(table : str, field : str, kind : str) -> any:
    res = []
    try:
        query = f"SELECT {field} FROM {table} WHERE {kind};"
        print(query)
        cur.execute(query)
        res = cur.fetchall()
        for row in res:
            print ("{}".format(row[0]))
        print("Field read sucessfully")
    except:
        print("read error")
    return res
