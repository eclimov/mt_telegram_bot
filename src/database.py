import sqlite3


class Database:
    def __init__(self, path):
        self.__con = sqlite3.connect(path, check_same_thread=False)
        self.__con.row_factory = sqlite3.Row
        self.__cur = self.__con.cursor()
        self.init_dables()

    def execute(self, sql, *args):
        self.__cur.execute(sql, args)
        self.__con.commit()
        return self.__cur

    def init_dables(self):
        sql_init_users = """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY UNIQUE NOT NULL, 
                first_name VARCHAR(40) NOT NULL,
                last_name VARCHAR(40) NOT NULL,
                phone_number VARCHAR(40) NOT NULL,
                when_authorized DATETIME 
            );
        """
        self.execute(sql_init_users)

        sql_init_activity_log = """
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY ASC AUTOINCREMENT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL DEFAULT 0,
                callback VARCHAR(40),
                message TEXT,
                update_query TEXT,
                when_created DATETIME NOT NULL
            );
        """
        self.execute(sql_init_activity_log)

        # Unauthorize users who exceed max authoization timespan
        sql_refresh_users = """
            UPDATE users
            SET users.when_authorized = NULL
            WHERE users.when_authorized < date('now','-7 days')
        """
        self.execute(sql_init_users)

    def __del__(self):
        self.__con.close()


'''
cur.execute('INSERT INTO users (...) VALUES(...)')
con.commit()
print(cur.lastrowid)
cur.execute('SELECT * FROM ...')
print(cur.fetchall())
'''

