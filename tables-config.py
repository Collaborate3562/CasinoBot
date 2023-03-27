import mysql.connector

# db = mysql.connector.connect(host = "localhost",user = "root",passwd = "",database = "test1")
db = mysql.connector.connect(user='root', password='',host='localhost',database = 'DB_AleekkCasino', auth_plugin='mysql_native_password')
cur = db.cursor()

def table():
    try:
        cur.execute("CREATE TABLE tbl_Users(id INT AUTO_INCREMENT Primary Key, RealName VARCHAR(50), UserName VARCHAR(100), UserID LONG, Wallet VARCHAR(42), Wagered FLOAT DEFAULT(0), Wins FLOAT DEFAULT(0),  ETH_Amount FLOAT DEFAULT(0), BNB_Amount FLOAT DEFAULT(0), JoinDate TIMESTAMP DEFAULT(CURRENT_TIMESTAMP) , UserAllowed bool DEFAULT(TRUE))")
        db.commit()
        print("Tables created sucessfully")
    except:
        print("tables error1")

table()

