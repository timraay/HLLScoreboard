import sqlite3

class DBConnection:
    def __init__(self, db_name):
        self.db = sqlite3.connect(db_name)
    def __enter__(self):
        return self.db.cursor()
    def __exit__(self, type, value, traceback):
        self.db.commit()
        self.db.close()