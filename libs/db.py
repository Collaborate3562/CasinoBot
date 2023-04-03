import mysql.connector
import datetime

db = mysql.connector.connect(user='root', password='',host='localhost',database = 'DB_AleekkCasino', auth_plugin='mysql_native_password')
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
        cur.execute(query)
        res = cur.fetchall()
    except:
        print("read error")
    return res

async def insertFields(table : str, field : dict) -> bool:
    bRes = False
    try:
        placeholders = ', '.join(['%s'] * len(field))
        columns = ', '.join(field.keys())

        query = "INSERT INTO %s ( %s ) VALUES ( %s )" % (table, columns, placeholders)
        print(query)

        cur.execute(query, list(field.values()))
        db.commit()

        bRes = True
        print("Field created sucessfully")
    except:
        print("read error")
    return bRes
