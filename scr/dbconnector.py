import psycopg as pg


class DBConnector:  # Connetion to the database class

    def __init__(self, dbname, user, password, address, config):

        self.dbname = dbname
        self.user = user
        self.password = password
        self.address = address

        self.conn = self.connect()
        self.cursor = self.conn.cursor()

        self.queries = {"get_table": ["SELECT * FROM ", " ORDER BY id"],
                        "value_exists": ["SELECT EXISTS(SELECT 1 FROM ", " WHERE ", " = '", "')"],
                        "get_columns": [
                            "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '",
                            "'"],
                        "get_user": ["SELECT * FROM users WHERE username = '", "'"],
                        "update_session_expire": ["UPDATE users SET session_expire = ", " WHERE username = '", "'"]}

        self.config = config

    def connect(self):  # getting the connection

        conn = None

        try:
            conn = pg.connect(dbname=self.dbname, user=self.user, password=self.password,
                              host=self.address[0], port=self.address[1])
        except Exception as err:
            print(err)

        return conn

    def get_table(self, tableName):  # get table from database by name, returns json

        logins = []

        queryRequestList = self.queries["get_table"]
        query = queryRequestList[0] + tableName + queryRequestList[1]

        self.cursor.execute(query)
        records = self.cursor.fetchall()

        queryRequestList = self.queries["get_columns"]
        query = queryRequestList[0] + tableName + queryRequestList[1]

        self.cursor.execute(query)
        columns = self.cursor.fetchall()

        for row in records:
            rowJson = {}
            for i in range(len(row)):
                rowJson[str(columns[i][0])] = (row[i])
            logins.append(rowJson)

        return logins

    def value_exists(self, tableName, value, key):  # check if value exist in certain place

        valueExists = False

        queryRequestList = self.queries["value_exists"]
        query = queryRequestList[0] + tableName + queryRequestList[1] + key + queryRequestList[2] + value + \
                queryRequestList[3]

        print(query)

        self.cursor.execute(query)
        valueExists = self.cursor.fetchall()[0][0]

        return valueExists

    def get_user_data(self, username):  # get user from users by it's username

        queryRequestList = self.queries["get_user"]
        query = queryRequestList[0] + username + queryRequestList[1]

        self.cursor.execute(query)
        userData = self.cursor.fetchall()[0]
        userDataJson = {}

        queryRequestList = self.queries["get_columns"]
        query = queryRequestList[0] + "users" + queryRequestList[1]

        self.cursor.execute(query)
        columns = self.cursor.fetchall()

        for i in range(len(userData)):
            userDataJson[str(columns[i][0])] = userData[i]

        return userDataJson

    def update_session_expire(self, username):

        userData = self.get_user_data(username)

        newSessionExpire = userData["session_expire"] + self.config.configData["session_lenght"]

        queryRequestList = self.queries["update_session_expire"]
        query = queryRequestList[0] + str(newSessionExpire) + queryRequestList[1] + username + queryRequestList[2]

        self.cursor.execute(query)
        self.conn.commit()

        return True

    def set_is_active(self, username, is_active):

        is_active = "true" if is_active else "false"
        self.cursor.execute("UPDATE users SET is_active = {} WHERE username = '{}'".format(is_active, username))

        self.conn.commit()

        return True

    def change_session(self, username, session, session_expire):

        self.cursor.execute("UPDATE users SET session = '{}' WHERE username = '{}'".format(session, username))
        self.cursor.execute(
            "UPDATE users SET session_expire = {} WHERE username = '{}'".format(session_expire, username))

        self.conn.commit()

        return True

    def change_nickname(self, username, nickname):

        self.cursor.execute("UPDATE users SET nickname = '{}' WHERE username = '{}'".format(nickname, username))
        self.conn.commit()

        return True

    def check_spelling(self, message):

        is_ok = True

        if message == "":
            is_ok = False
        if " " in message:
            is_ok = False
        if "'" in message:
            is_ok = False
        if not message.isascii():
            is_ok = False

        return is_ok