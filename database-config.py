import mysql.connector

# db = mysql.connector.connect(host = "localhost",user = "root",passwd = "bluesky0812",auth_plugin='mysql_native_password')
db = mysql.connector.connect(user='root', password='', host='localhost', auth_plugin='mysql_native_password')

cur = db.cursor()

def database():
    try:
        cur.execute("CREATE DATABASE DB_AleekkCasino")
        db.commit()
        print("Database created sucessfully!!")
        
    except:
        print("error")

database()











