import logging
import sqlite3
import sys

from settings import SQLITE_DB

SELECT_HECHIZO_FTS = "SELECT * FROM hechizos_fts WHERE search MATCH '{text}';"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SQLiteDB:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursorObj = self.connection.cursor()

        logger.info('Connection stablished with database: %s', db_file)

    def get_hechizo(self, text):
        logger.info('Python: %s - sqlite3: %s', sys.version, sqlite3.sqlite_version)
        query = SELECT_HECHIZO_FTS.format(text=text)

        self.cursorObj.execute(query)

        rows = self.cursorObj.fetchall()
        if rows:
            return rows[0]
        return

    def __exit__(self):
        self.cursorObj.close()
        self.connection.close()


sqlite_db = SQLiteDB(SQLITE_DB)

__all__ = ['sqlite_db']
