__author__ = 'francois'
from string import Template
import sqlite3
import numpy as np
import pandas as pd
import os

class Storage(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def prepare(self):
        pass

    def write_row(self, rowdict):
        pass

class PandasCsv(Storage):

    def __init__(self, database):
        self.data = pd.DataFrame()
        self.database = database
        self.rowlist = []

    def __enter__(self):
        if os.path.exists(self.database):
            self.data = pd.read_csv(self.database)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        newdata = pd.DataFrame(self.rowlist)
        print newdata
        d = pd.concat([self.data, newdata])
        d.to_csv(self.database)

    def prepare(self):
        pass

    def write_row(self, rowdict):
        self.rowlist.append(rowdict)

### Sqlite implementation ###

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

import io

def adapt_array(arr):
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    # http://stackoverflow.com/a/3425465/190597 (R. Hill)
    return buffer(out.read())


def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)

class Sqlite3(Storage):
    table = 'experiments'

    def __init__(self, database):
        # Converts np.array to TEXT when inserting
        sqlite3.register_adapter(np.ndarray, adapt_array)

        # Converts TEXT to np.array when selecting
        sqlite3.register_converter(TypeHelper.CUSTOM_ARRAY, convert_array)
        self.connection = sqlite3.connect(database, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

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


# import cmd
#
# class SqliteShell(cmd.Cmd):
#     PROMPT = "Sqlite (%s) > "
#     OUT = ">> %s"
#
#     def __init__(self, database, db):
#         cmd.Cmd.__init__(self)
#         self.prompt = self.PROMPT % database
#         self.db = db
#
#     def precmd(self, line):
#         """Hook method executed just before the command line is
#         interpreted, but after the input prompt is generated and issued.
#
#         """
#         return line
#
#     def postcmd(self, stop, line):
#         """Hook method executed just after a command dispatch is finished."""
#         return stop
#
#     def preloop(self):
#         """Hook method executed once when the cmdloop() method is called."""
#         pass
#
#     def postloop(self):
#         """Hook method executed once when the cmdloop() method is about to
#         return.
#
#         """
#         pass
#
#     def sql(self, arg):
#         if arg is not None:
#             try:
#                 print self.OUT % repr(self.db.read(arg))
#             except sqlite3.Error as e:
#                 print e.message
#
#     def disp_data(self, arg):
#         print self.db.table_info("experiments")
#         print self.db.table_content("experiments")
