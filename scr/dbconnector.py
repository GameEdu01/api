import psycopg as pg
from psycopg.rows import dict_row


class DBConnector:  # Connetion to the database class

    def __init__(self, dbname, user, password, address, config):

        self.dbname = dbname
        self.user = user
        self.password = password
        self.address = address

        self.conn = self.connect()
        self.cursor = self.conn.cursor(row_factory=dict_row)

        self.config = config

    def connect(self):  # getting the connection

        conn = None

        try:
            conn = pg.connect(dbname=self.dbname, user=self.user, password=self.password,
                              host=self.address[0], port=self.address[1])
        except Exception as err:
            print(err)

        return conn

    def get_table(self, table_name):  # get table from database by name, returns json

        query = "SELECT * FROM {}".format(table_name)

        self.cursor.execute(query)

        return self.cursor.fetchall()

    def value_exists(self, table_name, value, key):  # check if value exist in certain place

        self.cursor.execute("SELECT EXISTS(SELECT 1 FROM {} WHERE {} = '{}')".format(table_name, key, value))
        records = self.cursor.fetchone()

        return records["exists"]

    def get_value_from_string(self, table_name, value, key):  # check if value exist in certain place

        self.cursor.execute("SELECT * FROM {} WHERE {} = '{}'".format(table_name, key, value))
        records = self.cursor.fetchone()

        return records["exists"]

    def get_user_data(self, username, email=None):  # get user from users by it's username

        if email:

            query = "SELECT * FROM users WHERE email = '{}'".format(email)

            self.cursor.execute(query)

            return self.cursor.fetchone()

        query = "SELECT * FROM users WHERE username = '{}'".format(username)

        self.cursor.execute(query)

        return self.cursor.fetchone()

    def update_session_expire(self, username):

        userData = self.get_user_data(username)

        newSessionExpire = userData["session_expire"] + self.config.configData["session_lenght"]

        query = "UPDATE users SET session_expire = {} WHERE username = '{}'".format(newSessionExpire, username)

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
        self.cursor.execute("UPDATE users SET session_expire = {} WHERE username = '{}'".format(session_expire, username))

        self.conn.commit()

        return True

    def change_nickname(self, username, nickname):

        self.cursor.execute("UPDATE users SET nickname = '{}' WHERE username = '{}'".format(nickname, username))
        self.conn.commit()

        return True

    def signup_user(self, user, token, session, time_created):

        query = """INSERT INTO users (username, password, email, token, is_superuser, session, session_expire, is_active, money, time_spent_on_website)
                VALUES ('{}', '{}', '{}', '{}', false, '{}', {}, true, 0, 0)""".format(user.username, user.password,
                                                                                       user.email, token, session,
                                                                                       time_created + self.config.configData["session_length"])

        self.cursor.execute(query)
        self.conn.commit()

        return True

    def signup_user_wallet(self, user):

        query = f"""INSERT INTO m_users(name, surname, email, phone_number)
                        VALUES('{user.name}', '{user.surname}', '{user.email}', '{user.phone_number}')"""

        self.cursor.execute(query)
        self.conn.commit()

        return True
