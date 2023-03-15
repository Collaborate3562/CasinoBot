import mysql.connector

# db = mysql.connector.connect(host = "localhost",user = "root",passwd = "",database = "test1")
db = mysql.connector.connect(user='root', password='bluesky0812',host='localhost',database = 'DB_AleekkCasino', auth_plugin='mysql_native_password')
cur = db.cursor()

def table():
    try:
        cur.execute("CREATE TABLE tbl_Users(id INT AUTO_INCREMENT Primary Key, Name VARCHAR(50), UserName VARCHAR(100), UserID LONG, LastJooin Date, ETH_Amount FLOAT DEFAULT(0), BNB_Amount FLOAT DEFAULT(0), JoinDate TIMESTAMP DEFAULT(CURRENT_TIMESTAMP) , UserAllowed bool DEFAULT(TRUE))")
            # Type of room:
            #   1 A, 2 B1, 3 B2, 4 C, 5 101, 6 102, 7 201, 8 202, 9 full house
            # Booking source:
            #   1 Agoda, 2 booking, 3 directbooking
            # Payment:
            #   0 full, 1 deposit
        db.commit()
        print("Tables created sucessfully")
    except:
        print("tables error1")

table()

