__author__ = 'francois'
from string import Template
import sqlite3
import numpy as np
import pandas as pd
import os

def getLockFile(db):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), ".%s.db_lock"%db)

class Storage(object):
    def get_data(self):
        pass

class ProcessedStorage(Storage):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def prepare(self):
        pass

    def write_row(self, rowdict):
        pass

    def flush(self):
        pass


class RawStorage(Storage):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def prepare(self):
        pass

    def write_row(self, rowdict):
        pass

    def flush(self):
        pass

import zipfile
import tempfile
import shutil
import json


class Zip(RawStorage):

    CONFIG = "conf.json"


    def __init__(self, database, mode='w'):
        self.database = database + ".zip"
        self.zip = None
        self.data = None
        self.rowlist = []
        self.lock = FileLock(getLockFile(self.database))
        self.mode = mode

    def __enter__(self):
        if self.mode == 'w':
            self.lock.lock()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.mode == 'w':
            self.lock.unlock()

    def prepare(self):
        self.zip = zipfile.ZipFile(self.database, 'a', zipfile.ZIP_DEFLATED)

    def store(self, output_dir, conf, root):
        for key, value in conf.iteritems():
            conf[key] = os.path.relpath(value, output_dir)
        with open(os.path.join(output_dir, self.CONFIG), 'w') as f:
            json.dump(conf, f)

        for root_dir, dirs, files in os.walk(output_dir):
            for fi in files:
                path = os.path.join(root_dir, fi)
                self.zip.write(path, os.path.relpath(path, root))
        # self.zip.write(output_dir, os.path.relpath(output_dir, root))

    def get_data(self):
        if self.data is None:
            self.data = pd.DataFrame(self.rowlist).convert_objects(convert_dates=True, convert_numeric=True, convert_timedeltas=True)
        return self.data

    def get_results(self):
        if self.zip is None:
            self.zip = zipfile.ZipFile(self.database, 'r', zipfile.ZIP_DEFLATED)
        extract_dir = tempfile.mkdtemp()
        print "Writing to %s" % extract_dir
        self.zip.extractall(extract_dir)
        # results = []
        for output_dir, dirs, files in os.walk(extract_dir):
            if output_dir == extract_dir:
                continue
            with open(os.path.join(output_dir, self.CONFIG), 'r') as f:
                conf = json.load(f)
            for key, value in conf.iteritems():
                conf[key] = os.path.join(output_dir, value)
            yield (output_dir, conf)

        shutil.rmtree(extract_dir)

    def write_row(self, rowdict):
        self.rowlist.append(rowdict)


    def flush(self):
        self.zip.close()


class PandasHDF(ProcessedStorage):
    def __init__(self, database):
        self.data = pd.DataFrame()
        self.database = database + ".hd5"
        self.rowlist = []
        self.convert = None

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def prepare(self):
        pass

    def write_row(self, rowdict):
        self.rowlist.append(rowdict)

    def get_data(self):
        if self.data is None:
            if os.path.exists(self.database):
                self.data = pd.read_hdf(self.database, "dt")
        return self.data

    def flush(self):
        with FileLock(FileLock(getLockFile(self.database))) as lock:
            newdata = pd.DataFrame(self.rowlist)
            newdata.to_hdf(self.database, "dt", format = 't', append = True)

class PandasJson(ProcessedStorage):

    def __init__(self, database):
        self.data = pd.DataFrame()
        self.database = database+".json"
        self.rowlist = []
        self.convert = None

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def prepare(self):
        if os.path.exists(self.database):
            self.data = pd.read_json(self.database, orient = 'split')

    def write_row(self, rowdict):
        self.rowlist.append(rowdict)

    def get_data(self):
        if self.convert is None:
            self.convert = self.data.convert_objects(convert_dates=True, convert_numeric=True, convert_timedeltas=True)
        return self.convert

    def flush(self):
        with FileLock(FileLock(getLockFile(self.database))) as lock:
            newdata = pd.DataFrame(self.rowlist)
            d = pd.concat([self.data, newdata])
            d.to_json(self.database, orient = 'split')

class PandasPickle(ProcessedStorage):

    def __init__(self, database):
        self.data = pd.DataFrame()
        self.database = database+".pickle"
        self.rowlist = []
        self.convert = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def prepare(self):
        if os.path.exists(self.database):
            self.data = pd.read_pickle(self.database)

    def write_row(self, rowdict):
        self.rowlist.append(rowdict)

    def get_data(self):
        if self.convert is None:
            self.convert = self.data.convert_objects(convert_dates=True, convert_numeric=True, convert_timedeltas=True)
        return self.convert

    def flush(self):
        with FileLock(FileLock(getLockFile(self.database))) as lock:
            newdata = pd.DataFrame(self.rowlist)
            d = pd.concat([self.data, newdata])
            d.to_pickle(self.database)

from csv import QUOTE_ALL
from StringIO import StringIO

import cPickle

class PandasCsv(ProcessedStorage):

    ARRAY_TYPE = "np2darray"

    def __init__(self, database):
        self.data = None
        self.types = None
        self.database = database+".csv"
        self.rowlist = []
        self.create = False

    def __enter__(self):
        if os.path.exists(self.database):
            self.types = pd.read_csv(self.database, nrows = 1).iloc[0].to_dict()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def prepare(self):
        self.create = not os.path.exists(self.database)

    def flush(self):
        with FileLock(FileLock(getLockFile(self.database))) as lock:
            if not self.create:
                newdata = pd.DataFrame(self.rowlist)
            else:
                newdata = pd.DataFrame([self.types]+self.rowlist)
            newdata.to_csv(self.database, mode = 'a', index = False, header = self.create, quoting = QUOTE_ALL, line_terminator=";")

    def write_row(self, rowdict):
        if self.types is None:
            self.types = pd.DataFrame([rowdict]).dtypes.to_dict()
            for key, val in rowdict.iteritems():
                if type(val) is np.ndarray:
                    self.types[key] = self.ARRAY_TYPE

        for key, val in rowdict.iteritems():
            if type(val) is np.ndarray:
                rowdict[key] = self.dump_array(val)

        self.rowlist.append(rowdict)

    def get_data(self):
        if self.data is None:
            if os.path.exists(self.database):
                self.data = pd.read_csv(self.database, skiprows=[1], lineterminator=";")
                self.data.apply(self.pump_arrays, axis = 1)

        return self.data

    def pump_arrays(self, row):
        for key, val in self.types.iteritems():
            if val == self.ARRAY_TYPE:
                row[key] = self.load_array(row[key])
        return row

    def load_array(self, arr):
        return cPickle.loads(arr)
        # return np.loadtxt(StringIO(arr), delimiter="|")

    def dump_array(self, arr):
        return cPickle.dumps(arr)
        # out = StringIO()
        # np.savetxt(out, arr, delimiter="|")
        # return out.getvalue()

### Sqlite implementation ###
class TypeHelper(object):
    TXT = "TEXT"
    INT = "INT"
    FLOAT = "REAL"
    BLOB = "BLOB"
    ARRAY = "ARRAY"

    @classmethod
    def getType(cls, sample):
        if type(sample) is np.ndarray:
            return cls.ARRAY
        elif type(sample) in [basestring, str]:
            return cls.getTypeFromString(sample)
        elif type(sample) in (float, np.float_):
            return cls.FLOAT
        elif type(sample) is int:
            return cls.INT
        elif type(sample) is bool:
            return cls.TXT
        return cls.BLOB

    @classmethod
    def getTypeFromString(cls, s):
        try:
            float(s)
            return cls.FLOAT
        except ValueError:
            pass

        try:
            import unicodedata

            d = unicodedata.numeric(s)
            if type(d) == float:
                return cls.FLOAT
            elif type(d) == int:
                return cls.INT
        except (TypeError, ValueError):
            pass

        return cls.TXT

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

class Sqlite3(ProcessedStorage):
    table = 'experiments'

    def get_data(self):
        return self.connection

    def __init__(self, database):
        # Converts np.array to TEXT when inserting
        sqlite3.register_adapter(np.ndarray, adapt_array)

        # Converts TEXT to np.array when selecting
        sqlite3.register_converter(TypeHelper.ARRAY, convert_array)
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


    def lock(self):
        self.fp = open(self.file, 'w')
        # try:
        fcntl.lockf(self.fp, fcntl.LOCK_EX)

    def unlock(self):
        fcntl.lockf(self.fp, fcntl.LOCK_UN)
        self.fp.close()

    def __enter__(self):
        self.lock()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unlock()


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
