import pymysql as sql


class mysql:
    def __init__(self):
        try:
            self.connect_db()
            # print("Database connected!")
        except:
            print("Connection failed!")
            raise ConnectionError

    def connect_db(self):
        self.db = sql.connect(host="wowstats.cctqbu5psiq5.us-east-2.rds.amazonaws.com", port=3306, user="moliangzhou",
                              password="33906413", database="wowstats")

    def get_IDlist(self):
        cursor = self.db.cursor()
        getid_sql = """SELECT `accountID` FROM wowstats.`wows_stats`"""
        try:
            # execute sql in database
            cursor.execute(query=getid_sql)
            return cursor.fetchall()
        except:
            # roll back if error
            self.db.rollback()
            print("Fetch failed!!!")

    def write_ID(self, data_list):
        cursor = self.db.cursor()
        insert_sql = """INSERT INTO `wowstats`.`wows_stats` (`accountID`, `nickname`) VALUES %s"""
        for record in data_list:
            try:
                # execute sql in database
                cursor.execute(query=insert_sql, args=[record])
                self.db.commit()
                print("%s written." % (record,))
            except:
                # roll back if error
                self.db.rollback()
                print("%s write failed!" % (record,))
        print("********************Database write finished********************")

    def write_detail(self, data_list):
        cursor = self.db.cursor()
        update_sql = """
        UPDATE `wowstats`.`wows_stats`
        SET `nickname` = %s,`total` = %s, `win`= %s, `defeat`= %s, `draw`= %s
        WHERE `accountID`=%s
        """
        for record in data_list:

            try:
                # execute sql in database
                cursor.execute(query=update_sql,
                               args=[record[1], record[2], record[3], record[4], record[5], record[0]])
                self.db.commit()
                print("%s written." % (record,))
            except:
                # roll back if error
                self.db.rollback()
                print("%s write failed!" % (record,))
        print("********************Database write finished********************")

    def close_db(self):
        # disconnect
        self.db.close()


if __name__ == '__main__':
    try:
        db = mysql()
        db.write_detail(data_list=[('1018170999', 'Luizclv', '0', '0', '0', '0')])
        db.close_db()
    except ConnectionError:
        print("Database connection failed!")
