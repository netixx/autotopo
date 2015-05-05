__author__ = 'francois'
from string import Template
import sqlite3


class Storage(object):
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def prepare(self):
        pass

    def write_row(self, rowdict):
        pass


class Sqlite3(Storage):
    table = 'experiments'

    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

    def prepare(self):
        self._prepare_base()

    def write_row(self, rowdict):
        self._add_cols(rowdict)
        self._write_results(rowdict)

    def __write(self, cmd, subst=None):
        c = self.connection.cursor()
        if subst is None:
            c.execute(cmd)
        else:
            c.execute(cmd, subst)
        self.connection.commit()

    def read(self, cmd, subst=None):
        c = self.connection.cursor()
        if subst is None:
            c.execute(cmd)
        else:
            c.execute(cmd, subst)
        return c.fetchall()

    def _add_column(self, table, colname, type="TEXT"):
        try:
            self.__write(Template('''ALTER TABLE "$table" ADD COLUMN "$colname" $type;''').substitute(table=table,
                                                                                                      colname=colname,
                                                                                                      type=type))
        except sqlite3.OperationalError as e:
            # print e
            pass

    def table_exists(self, table):
        return self.read('''SELECT name FROM sqlite_master WHERE type="table" AND name='%s';''' % table)

    def _prepare_base(self):
        if not self.table_exists("experiments"):
            self.__write('''CREATE TABLE %s (exp_id INTEGER, PRIMARY KEY(exp_id ASC));''' % self.table)

    def _add_cols(self, rowdict):
        for col, val in rowdict.iteritems():
            self._add_column(self.table, col, TypeHelper.getType(val))

    def _write_results(self, results):
        cmd = '''INSERT INTO experiments('%s') VALUES (%s);'''
        xs = ", ".join(["?"] * len(results))
        # print cmd%("','".join(results.keys()), xs)
        self.__write(cmd % ("','".join(results.keys()), xs), results.values())


    def printTable(self):
        tables = self.read('''SELECT name FROM sqlite_master WHERE type='table';''')
        res = ""
        if tables[0] is None:
            return "No tables found (db is empty)..."
        for table in tables[0]:
            res += "Table '%s' :[%s]\n" % (table, self.table_info(table))
        return res

    def table_info(self, table):
        return ", ".join(zip(*self.read('''PRAGMA TABLE_INFO(%s);''' % table))[1])

    def table_content(self, table):
        return self.read('''SELECT * FROM %s''' % table)


import fcntl


class FileLock(object):
    def __init__(self, file):
        self.file = file

    def __enter__(self):
        self.fp = open(self.file, 'w')
        # try:
        fcntl.lockf(self.fp, fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        fcntl.lockf(self.fp, fcntl.LOCK_UN)
        self.fp.close()


import numpy as np


class TypeHelper(object):
    SQLITE_TXT = "TEXT"
    SQLITE_INT = "INT"
    SQLITE_FLOAT = "REAL"
    SQLITE_BLOB = "BLOB"
    CUSTOM_ARRAY = "ARRAY"

    @classmethod
    def getType(cls, sample):
        if type(sample) is np.ndarray:
            return cls.CUSTOM_ARRAY
        elif type(sample) in [basestring, str]:
            return cls.getTypeFromString(sample)
        elif type(sample) in (float, np.float_):
            return cls.SQLITE_FLOAT
        elif type(sample) is int:
            return cls.SQLITE_INT
        elif type(sample) is bool:
            return cls.SQLITE_TXT
        return cls.SQLITE_BLOB

    @classmethod
    def getTypeFromString(cls, s):
        try:
            float(s)
            return cls.SQLITE_FLOAT
        except ValueError:
            pass

        try:
            import unicodedata

            d = unicodedata.numeric(s)
            if type(d) == float:
                return cls.SQLITE_FLOAT
            elif type(d) == int:
                return cls.SQLITE_INT
        except (TypeError, ValueError):
            pass

        return cls.SQLITE_TXT

    @staticmethod
    def is_number(s):
        try:
            return float(s)
        # return True
        except ValueError:
            pass

        try:
            import unicodedata

            return unicodedata.numeric(s)
        # return True
        except (TypeError, ValueError):
            pass

        return False
