import mysql.connector

db = mysql.connector.connect(host = "localhost", user = "root", passwd = "", database = "DB_AleekkCasino")
cur = db.cursor()

def table():
    try:
        cur.execute("CREATE TABLE tbl_users(id INT AUTO_INCREMENT Primary Key, RealName VARCHAR(50), UserName VARCHAR(100), UserID LONG, Wallet VARCHAR(42), ETH_Wagered FLOAT DEFAULT(0), BNB_Wagered FLOAT DEFAULT(0), ETH_Wins FLOAT DEFAULT(0), BNB_Wins FLOAT DEFAULT(0), ETH_Amount FLOAT DEFAULT(0), BNB_Amount FLOAT DEFAULT(0), JoinDate TIMESTAMP DEFAULT(CURRENT_TIMESTAMP) , UserAllowed bool DEFAULT(TRUE), ReadyTransfer bool DEFAULT(FALSE), Deployed_ETH bool DEFAULT(FALSE), Deployed_BSC bool DEFAULT(FALSE))")
        db.commit()
        print("Tables created sucessfully")
    except:
        print("Tables created failed")

table()

