import pymysql as sql


class mysql:
    def __init__(self):
        try:
            self.connect_db()
        except:
            print("Connection failed!")
            raise ConnectionError

    def connect_db(self):
        self.db = sql.connect(host="localhost", user="root", password="33906413", database="wows_stats")
        print("Database connected!")

    def write_db(self, data):
        cursor = self.db.cursor()
        insert_sql = """INSERT INTO `account` (`account ID`, `nickname`) VALUES %s"""
        for id in data["data"]:
            if data["data"][id] is not None:
                nickname = data["data"][id]["nickname"]
                record = (str(id), str(nickname))
                try:
                    # 执行sql语句
                    cursor.execute(query=insert_sql, args=[record])
                    self.db.commit()
                except:
                    # 如果发生错误则回滚
                    self.db.rollback()
        # # 提交到数据库执行
        # cursor.execute("SELECT * FROM wows_stats.account")
        # # 提交到数据库执行
        # alldata = cursor.fetchall()
        # print(alldata)

    def close_db(self):
        # 关闭数据库连接
        self.db.close()


if __name__ == '__main__':
    try:
        db = mysql()
        db.write_db(data="")
        db.close_db()
    except ConnectionError:
        print("Database connection failed!")
