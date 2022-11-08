import functools
import sqlite3
import urllib.request

URL_OTL = r"https://wegenenverkeer.data.vlaanderen.be/doc/implementatiemodel/master/html/OTL.db"


class OTLCursorPool:
    """
    Single source for connections and cursors to the OTL SQLite database.
    Lazily fetches and caches the latest version of the SQLite database file.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = super(OTLCursorPool, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    @functools.cached_property
    def _db_file(self):
        """
        Cached property for SQLite database file.

        :return: tempfile containing OTL SQLite database
        """
        db_file, _ = urllib.request.urlretrieve(URL_OTL)
        return db_file

    def get_connection(self):
        """
        Create and return a read-only connection with the local OTL SQLite database.

        :return: An open SQLite database represented by a sqlite3.Connection object
        """
        return sqlite3.connect(f'file:{self._db_file}?mode=ro', uri=True)

    def get_cursor(self):
        """
        Create and return a Cursor object for the local OTL SQLite database.

        :return: A cursor represented by a sqlite3.Cursor object.
        """
        return self.get_connection().cursor()


otl_cursor_pool = OTLCursorPool()
connection = otl_cursor_pool.get_connection()
print("Done")

#db_filename, headers = urlretrieve(r"https://wegenenverkeer.data.vlaanderen.be/doc/implementatiemodel/master/html/OTL.db")
#con = sqlite3.connect(db_filename)
#cur = con.cursor()
#res = cur.execute("""SELECT c.name, c.deprecated_version
#FROM OSLOClass as c
#WHERE c.deprecated_version IS NOT NULL AND c.deprecated_version != '' """)
#print(res.fetchone())
