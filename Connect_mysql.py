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

    def write_db(self, data_list):
        cursor = self.db.cursor()
        insert_sql = """INSERT INTO `wows_account` (`account ID`, `nickname`) VALUES %s"""
        for record in data_list:
            self.write_single(insert_sql=insert_sql, record=record, cursor=cursor)
        print("********************Database write finished********************")

    def write_single(self, insert_sql, record, cursor):
        try:
            # 执行sql语句
            cursor.execute(query=insert_sql, args=[record])
            self.db.commit()
            print("%s written." % (record,))
        except:
            # 如果发生错误则回滚
            self.db.rollback()
            print("%s write failed!" % (record,))

    def close_db(self):
        # 关闭数据库连接
        self.db.close()


if __name__ == '__main__':
    try:
        db = mysql()
        # db.write_db(data="")
        db.close_db()
    except ConnectionError:
        print("Database connection failed!")
