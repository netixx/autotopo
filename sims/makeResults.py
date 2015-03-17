#!/usr/bin/python2.7

import csv
import numpy as np
from string import Template

RESULT_COLNAME_TPL=Template("${var}_${col}_${func}")


HIST_PARAMS = {
    'min' : 0,
    'max' : 20,
    'nbins' : 12
}


# EXP_PARAMETERS = {
#
# }

#format : {var : {column :[ functions/treatment]}}
EXP_RESULTS = {
    "speed" :
        {
            "avg" : ["avg", "std", "cdf"]
        },
    "acc" :
        {
            "cumulatedPlus" : ["avg", "cdf"],
            "cumulatedMinus" : ["avg", "cdf"]
        },
    "agentConn" :
        {
            "connect" : ["avg", "min", "max", "cdf"]
        },
    "agentInstConn" :
        {
            "avg" : ["avg", "cdf"],
            "max" : ["max"]
        },
    "roadConn" :
        {
            "connect" : ["sum"]
        },
    "roadInstConn" :
        {
            "avg" : ["sum"],
            },
    "time" :
        {
            "time" : ['avg', 'cdf']
        },
    "timeAgentConn" :
        {
           "avg" : ['avg', 'cdf'],
           ("time", "avg") : ["xy"]
        },
    "timeRoadConn" :
        {
            "avg": ['avg', 'cdf'],
            ("time", "avg"): ["xy"]
        }
}

FILES= {
    "speed" : ["id","avg","std", "max", "min"],
    "acc" : ["id", "cumulatedMinus", "cumulatedPlus", "avg", "std", "max", "min"],
    "agentConn" : ['id', 'connect'],
    "agentInstConn" : ["id","avg","std","max","min"],
    "roadConn" : ["id", "connect"],
    "roadInstConn" : ["id","avg","std","max","min"],
    "time": ["id","entry","exit","time"],
    "timeAgentConn":["time", "avg", "std", "max", "min"],
    "timeRoadConn" : ["time", "avg", "std", "max", "min"]
}

NAME_MAP= {
    "acc" : "acceleration.csv",
    "agentConn" : "agentConnections.csv",
    "agentInstConn" : "agentsInstantConnections.csv",
    "roadConn" : "roadSegmentConnections.csv",
    "roadInstConn" : "roadSegmentInstantConnections.csv",
    "speed" : "speed.csv",
    "time" : "time.csv",
    "timeAgentConn" : "timeAgentsInstantConnections.csv",
    "timeRoadConn" : "timeSegmentInstantConnections.csv"
    }

class CsvReader():

    def __init__(self, file, cols):
        self.cols = {col:i for i, col in enumerate(cols)}
        with open(file, 'r') as f:
            reader = csv.reader(f, delimiter = ";", quotechar = '"')
            r = [row for row in reader]
            self.data = np.array(r[1:], dtype = float)
            self.cols = {col:i for i, col in enumerate(r[0])}

    def _colToNum(self, col):
        return self.cols[col]

    def getColumn(self, col):
        return self.data[:,self._colToNum(col)]

    def getColumns(self, cols):
        nCols = [self._colToNum(col) for col in cols]
        return self.data[:, nCols][1:]


class _FuncHelper(type):
    import numpy as np
    np = np

    ARRAY_FUNCS = ['hist', 'cdf', 'xy']
    TUPLE_FUNCS = ['xy']

    @classmethod
    def cdf(cls, data):
        s = cls.np.sort(data)
        # s = cls.jitter(s)
        yvals = (cls.np.arange(len(s)) + 0.5) / float(len(s))
        return cls.np.array([s, yvals])

    @classmethod
    def hist(cls, data):
        # bins = cls.np.linspace(HIST_PARAMS['min'], HIST_PARAMS['max'], HIST_PARAMS['nbins'])
        hist, bin_edges = cls.np.histogram(data, HIST_PARAMS['nbins'])
        return cls.np.array([bin_edges, hist])

    @classmethod
    def xy(cls, data):
        x, y = data
        return cls.np.array([x, y])

    FUNC_MAP = {
        "avg": np.average,
        "min": np.min,
        "max": np.max,
        "hist": hist,
        "sum": np.sum,
        "cdf": cdf,
        "std": np.std,
        "xy" : xy
    }

    def __getattr__(cls, item):
        return cls.FUNC_MAP[item]

class FuncHelper(object):
    """Properties for making graphs and interface to graph object"""
    __metaclass__ = _FuncHelper

class TypeHelper(object):
    SQLITE_TXT = "TEXT"
    SQLITE_INT = "INT"
    SQLITE_FLOAT = "REAL"
    SQLITE_BLOB = "BLOB"
    CUSTOM_ARRAY = "ARRAY"

    @classmethod
    def getType(cls, s):
        if type(s) is basestring:
            return cls.getTypeFromString(s)
        elif type(s) is np.array:
            return cls.CUSTOM_ARRAY
        elif type(s) is float:
            return cls.SQLITE_FLOAT
        elif type(s) is int:
            return cls.SQLITE_INT
        return cls.SQLITE_BLOB

    @classmethod
    def getTypeFromString(cls, s):
        try:
            bool(s)
            return cls.SQLITE_INT
        except ValueError:
            pass

        try:
            int(s)
            return cls.SQLITE_INT
        except ValueError:
            pass

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
        #             return True
        except ValueError:
            pass

        try:
            import unicodedata
            return unicodedata.numeric(s)
        #             return True
        except (TypeError, ValueError):
            pass

        return False


def db_write(cmd, subst = None):
    c = connection.cursor()
    if subst is None:
        c.execute(cmd)
    else:
        c.execute(cmd, subst)
    connection.commit()

def db_read(cmd, subst = None):
    c = connection.cursor()
    if subst is None:
        c.execute(cmd)
    else:
        c.execute(cmd, subst)
    return c.fetchall()

def db_add_column(table, colname, type="TEXT"):
    try:
        db_write(Template('''ALTER TABLE "$table" ADD COLUMN "$colname" $type;''').substitute(table = table,
                                                                                              colname = colname, type = type))
    except sqlite3.OperationalError:
        pass

def db_table_exists(table):
    return db_read('''SELECT name FROM sqlite_master WHERE type="table" AND name='%s';'''%table)

def db_prepare_base():
    if not db_table_exists("experiments"):
        db_write('''CREATE TABLE experiments (exp_id INTEGER, PRIMARY KEY(exp_id ASC));''')

def db_prepare_parameters(params):
    #learn vars and types from read parameters
    for arg, val in params.iteritems():
        db_add_column('experiments', arg, TypeHelper.getType(val))

def exp_res_to_colname(var, col, func):
    return RESULT_COLNAME_TPL.substitute(var = var,
                                         col = col,
                                         func = func)

def db_prepare_results(results):
    for var, dvar in EXP_RESULTS.iteritems():
        for col, funcs in dvar.iteritems():
            for func in funcs:
                if func in FuncHelper.TUPLE_FUNCS:
                    cname = "_".join(col)
                else:
                    cname = col
                colname = exp_res_to_colname(var, cname, func)
                if func in FuncHelper.ARRAY_FUNCS:
                    type = TypeHelper.CUSTOM_ARRAY
                else:
                    type = TypeHelper.SQLITE_FLOAT

                db_add_column('experiments', colname, type)


def db_prepare_scenario(scenario):
    for arg, val in scenario.iteritems():
        db_add_column('experiments', arg, TypeHelper.getType(val))


def db_write_results(results):
    cmd = '''INSERT INTO experiments('%s') VALUES (%s);'''
    xs = ", ".join(["?"]*len(results))
    # print cmd%("','".join(results.keys()), xs)
    db_write(cmd%("','".join(results.keys()), xs), results.values())


def db_print():
    tables = db_read('''SELECT name FROM sqlite_master WHERE type='table';''')
    res = ""
    if tables[0] is None:
        return "No tables found (db is empty)..."
    for table in tables[0]:
        res += "Table '%s' :[%s]\n"%(table, db_table_info(table))
    return res

def db_table_info(table):
    return ", ".join(zip(*db_read('''PRAGMA TABLE_INFO(%s);'''%table))[1])

def db_table_content(table):
    return db_read('''SELECT * FROM %s'''%table)

def getResults(dir):
    import os.path as path
    data = {}
    #load data from files
    for name, file in NAME_MAP.iteritems():
        data[name] = CsvReader(path.join(dir,file), FILES[name])

    return data


def getParameters(propfile):
    d = {}
    with open(propfile, "r") as f:
        for line in f:
            if not line.startswith("#") and len(line) > 1:
                tuple = line.strip().partition("=")
                d[tuple[0]] = tuple[2]
    return d


def getScenario(scenario):
    from xml.dom import minidom
    out = {"scenario" : scenario}
    xmldoc = minidom.parse(scenario)
    sc = xmldoc.getElementsByTagName('Simulation')[0]
    out['duration'] = float(sc.getAttribute('duration'))
    roads = sc.getElementsByTagName('Road')
    meanqval = []
    meanqw = []
    meanspeedval = []
    meanspeedw = []
    for road in roads:
        roadid = road.getAttribute('id')
        inflows = road.getElementsByTagName('Inflow')
        vs = []
        qs = []
        for inflow in inflows:
            vs.append((inflow.getAttribute('t'), (inflow.getAttribute('v'))))
            qs.append((inflow.getAttribute('t'), (inflow.getAttribute('q_per_hour'))))
        vs = np.array(vs, dtype=float).transpose()
        qs = np.array(qs, dtype = float).transpose()
        out['inflow_speed_%s'%roadid] = vs
        out['inflow_q_%s' % roadid] = qs
        meanqval.append(np.trapz(y=qs[1], x=qs[0]))
        meanqw.append(qs[0].max()-qs[0].min())
        meanspeedval.append(np.trapz(y=vs[1], x=vs[0]))
        meanspeedw.append(vs[0].max()-vs[0].min())
    # print meanflow
    out['inflow_mean_speed'] = np.average(meanspeedval, weights= meanspeedw)/np.mean(meanspeedw)
    out['inflow_mean_q'] = np.average(meanqval, weights = meanqw)/np.mean(meanqw)

    return out

def makeResults(params, scenario, data):
    dt = {}
    #leave params as is
    for name, values in data.iteritems():
        for col, funcs in EXP_RESULTS[name].iteritems():
            for func in funcs:
                #tuple of columns for xy
                if func in FuncHelper.TUPLE_FUNCS:
                    r = getattr(FuncHelper, func)((values.getColumn(c) for c in col))
                    cname = "_".join(col)
                else:
                    r = getattr(FuncHelper, func)(values.getColumn(col))
                    cname = col

                dt[exp_res_to_colname(name, cname, func)] = r
    # print dt
    return dict(params.items()+dt.items()+scenario.items())

import cmd
class SqliteShell(cmd.Cmd):
    PROMPT = "Sqlite (%s) > "
    OUT = ">> %s"

    def __init__(self, database, connection):
        cmd.Cmd.__init__(self)
        self.prompt = self.PROMPT % database
        self.connection = connection

    def precmd(self, line):
        """Hook method executed just before the command line is
        interpreted, but after the input prompt is generated and issued.

        """
        return line

    def postcmd(self, stop, line):
        """Hook method executed just after a command dispatch is finished."""
        return stop

    def preloop(self):
        """Hook method executed once when the cmdloop() method is called."""
        pass

    def postloop(self):
        """Hook method executed once when the cmdloop() method is about to
        return.

        """
        pass

    def do_sql(self, arg):
        if arg is not None:
            try:
                print self.OUT % repr(db_read(arg))
            except sqlite3.Error as e:
                print e.message

    def do_disp_data(self, arg):
        print db_table_info("experiments")
        print db_table_content("experiments" )


class _PyplotGraph(type):
    """Interface with the pyplot object"""

    def __new__(mcs, *args, **kwargs):
        # import pyplot and register  it
        import matplotlib.pyplot as plt

        mcs.plt = plt
        return type.__new__(mcs, *args, **kwargs)

    def __getattr__(cls, item):
        def decorate(*args, **kwargs):
            o = getattr(cls.plt, item)(*args, **cls.decorate(g_filtering = True, **kwargs))
            cls.decorate(**kwargs)
            return o

        return decorate

    # def subplot3d(cls, *args):
    #     from mpl_toolkits.mplot3d import Axes3D
    #
    #     return cls.plt.subplot(*args, projection = '3d')

    def decorate(cls, axes = None, g_filtering = False, g_grid = False, g_xtickslab = None, g_xticks = None,
                 g_xlabel = None, g_ylabel = None, g_zlabel = None, g_title = None, g_xgrid = False, g_ygrid = False, g_ylogscale = False,
                 g_ylim = None,
                 **kwargs):

        if g_filtering:
            return kwargs
        if axes is None:
            ax = cls.plt.gca()
        else:
            ax = axes
        if g_grid:
            g_xgrid = True
            g_ygrid = True
        if g_xgrid:
            ax.xaxis.grid(True, linestyle = '-', which = 'major', color = 'lightgrey', alpha = 0.4)
        if g_ygrid:
            ax.yaxis.grid(True, linestyle = '-', which = 'major', color = 'lightgrey', alpha = 0.5)
        if g_xlabel:
            # cls.plt.xlabel(g_xlabel)
            ax.set_xlabel(g_xlabel)
        if g_ylabel:
            # cls.plt.ylabel(g_ylabel)
            ax.set_ylabel(g_ylabel)
        if g_zlabel:
            # cls.plt.zlabel(g_zlabel)
            ax.set_zlabel(g_zlabel)
        if g_title:
            ax.set_title(g_title)
            # cls.plt.title(g_title)
        if g_xticks:
            ax.set_xticks(g_xticks)
            # cls.xticks(g_xticks)
        if g_xtickslab:
            ax.set_xticklabels(g_xtickslab)
        if g_ylogscale:
            cls.plt.yscale('log', nonposy = 'clip')
            # ax.set_yscale('log', nonposy='clip')
        if g_ylim:
            cls.plt.ylim(g_ylim)

import collections
import textwrap

class CsvBackend(object):
    pass

class GraphBackend(object):
    """Properties for making graphs and interface to graph object"""

    __metaclass__ = _PyplotGraph

    import random as rand

    colors = ['b', 'g', 'c', 'm', 'y', 'k', 'aqua', 'blueviolet', 'brown',
              'cadetblue', 'chartreuse', 'chocolate', 'coral', 'cornflowerblue', 'crimson',
              'darkblue', 'darkcyan', 'darkgrey', 'darkgreen', 'darkslateblue', 'darkgoldenrod', 'darkturquoise',
              'deeppink', 'dodgerblue', 'firebrick', 'forestgreen', 'fuchsia', 'green', 'greenyellow', 'hotpink',
              'indianred', 'indigo', 'lightseagreen', 'lightsalmon', 'limegreen', 'maroon', 'mediumaquamarine', 'mediumblue',
              'mediumvioletred', 'mediumslateblue', 'navy', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 'purple', 'royalblue',
              'seagreen', 'slateblue', 'sienna', 'steelblue', 'teal', 'tomato']
    rand.shuffle(colors)
    markers = ['^', 'd', 'o', 'v', '>', '<', 'p', 's', '*']

    alpha = 0.9
    # alpha3d = 0.85
    # alphaSurf = 0.7

    graphWidth = 10
    _grHeight = 4
    _titleHeight = 1.5

    @classmethod
    def getColor(cls, item = None):
        """Get a color for item
        returns random color if item is none
        :param item: hash item to get color
        """
        if item is None or not isinstance(item, collections.Hashable):
            return cls.colors[cls.rand.randint(0, len(cls.colors) - 1)]
        return cls.colors[hash(item) % len(cls.colors)]

    @classmethod
    def getMarker(cls, item = None):
        if item is None or not isinstance(item, collections.Hashable):
            return cls.markers[cls.rand.randint(0, len(cls.markers) - 1)]
        return cls.markers[hash(item) % len(cls.markers)]

    @classmethod
    def graphHeight(cls, nGraphs = 1):
        return cls._grHeight * nGraphs + cls._titleHeight

    @staticmethod
    def setMargins(graph):
        margins = list(graph.margins())
        if margins[0] < 0.05:
            margins[0] = 0.05
        if margins[1] < 0.05:
            margins[1] = 0.05
        # self.gr.margins(x = 0.05, y = 0.05)
        graph.margins(*margins)


    @classmethod
    def removeScale(cls, scaleDict, values):
        o = []
        for i, value in enumerate(values):
            if not scaleDict.has_key(value):
                scaleDict[value] = len(scaleDict) + 1
            o.append(scaleDict[value])

        return o


    @classmethod
    def setLegend(cls):
        # cls.legend(loc = 'upper left')#, bbox_to_anchor = (0, 0))
        return cls.legend(loc = 'center left', bbox_to_anchor = (1, 0.5))
        # clsbbox_extra_artists = (lgd,), bbox_inches = 'tight')

    @classmethod
    def make(cls, figure, x, y, yerr = None, legend = None):
        if legend is not None:
            cls.errorbar(x, y, yerr = yerr, label = legend)
        else:
            cls.errorbar(x, y, yerr = yerr)


    @classmethod
    def newFigure(cls):
        return cls.figure()

    @classmethod
    def saveFigure(cls, document, figure):
        # for ax in figure.get_axes():
        #     ax.set_position([0.1, 0.1, 0.5, 0.8])
        document.savefig(figure, bbox_inches = 'tight', bbox_extra_artist=[cls.setLegend()])

    #file related methods

    @staticmethod
    def newFile(path):
        from matplotlib.backends.backend_pdf import PdfPages

        print('Creating new graph at %s\n' % path)
        return PdfPages(path)

    @staticmethod
    def close(pdf):
        import datetime

        d = pdf.infodict()
        d['Title'] = 'AutoTopo'
        d['Author'] = u'Francois Espinet'
        d['Subject'] = 'AutoTopo'
        d['Keywords'] = 'autotopo'
        d['ModDate'] = datetime.datetime.today()
        pdf.close()
        print("Graph successfully written")


# def logGraph(func):
#     def f(self, **kwargs):
#         print("Making new graph %s with %s%s%s ... " % (
#             func.__name__,
#             "variables : %s" % self.printVariables(kwargs['variables']) if kwargs.has_key('variables') and len(kwargs['variables']) > 0 else "",
#             ", parameters: %s" % self.printParams(kwargs['parameters']) if kwargs.has_key('parameters') and len(kwargs['parameters']) > 0 else "",
#             ", filtering: %s" % self.printParams(kwargs['filtering']) if kwargs.has_key('filtering') and len(kwargs['filtering']) > 0 else "")
#         )
#         func(self, **kwargs)
#         print("done\n")
#
#     return f



class Graph(object):
    backend = GraphBackend

    TITLE_WRAP_WIDTH = 60
    LEGEND_WRAP_WIDTH = 30

    class QueryBuilder(object):

        # class And(object):
        #     pass
        #
        # class Or(object):
        #     pass
        #
        KW_AND = "AND"
        KW_OR = "OR"
        KW_GE = ">="
        KW_GT = ">"
        KW_EQ = "=="
        KW_LE = "<="
        KW_LT = "<"
        LP = "("
        RP = ")"
        KW_DISTINCT = "DISTINCT"

        tpl = Template('''SELECT $distinct $select_what FROM $table $where $group_by;''')

        def __init__(self, table = "experiments"):
            self._select_what = []
            self._select_table = table
            self._select_where = []
            self._group_by = []
            self.distinct = False

        def quote(self, exp):
            return '"%s"'%exp

        def getMap(self):
            return {s: i for i, s in enumerate(self._select_what)}

        # @staticmethod
        # def formatList(lst):
        #     return ", ".join(lst)

        def select(self, val):
            if type(val) is basestring:
                self._select_what.append(self.quote(val))
            elif type(val) is dict:
                for k in val.iterkeys():
                    self.select(k)
            return self

        def where(self, what, cond):
            qwhat = self.quote(what)
            if cond is None:
                pass
            elif type(cond) in (list, tuple):
                cs = sorted(cond)
                self._select_where.extend((self.LP, qwhat, self.KW_GE, self.quote(cs[0]), self.KW_AND, qwhat, self.KW_LE, self.quote(cs[1]), self.RP))
            else:
                self._select_where.extend((self.LP, qwhat, self.KW_EQ, self.quote(cond), self.RP))

            self._select_what.append(what)
            return self

        def groupby(self, what, cond = None):
            if cond is None:
                self._group_by.append(what)
            else:
                self.cand().where(what, cond).groupby(what)
            return self


        def cand(self):
            if len(self._select_where) > 0:
                self._select_where.append(self.KW_AND)
            return self

        def ands(self, dct):
            return self._conjs(dct, self.KW_AND)
            # self._select_where.extend(list(self.KW_AND.join(it)))

        def ors(self, dct):
            return self._conjs(dct, self.KW_OR)
            # self._select_where.extend(list(self.KW_OR.join(it)))

        def _conjs(self, dct, conj):
            for ki, condi in dct.iteritems():
                if condi is not None:
                    if conj == self.KW_AND:
                        self.cand()
                    else:
                        self.cor()
                self.where(ki, condi)



        def cor(self):
            if len(self._select_where) > 0:
                self._select_where.append(self.KW_OR)
            return self

        def openp(self):
            if len(self._select_where) > 0:
                self._select_where.append(self.LP)
            return self

        def closep(self):
            if len(self._select_where) > 0:
                self._select_where.append(self.RP)
            return self

        def build(self):
            return self.tpl.substitute(distinct = self.KW_DISTINCT if self.distinct else "",
                                        select_what = '"%s"'%'", "'.join(self._select_what) if len(self._select_what) >0 else "*",
                                       table = self._select_table,
                                       where = "WHERE %s"%" ".join(str(t) for t in self._select_where) if len(self._select_where) > 0 else "",
                                       group_by = "GROUP BY (%s)"%", ".join(self._group_by) if len(self._group_by) > 0 else "")


    @classmethod
    def wrapTitle(cls, title):
        return "\n".join(textwrap.wrap(title, cls.TITLE_WRAP_WIDTH))

    @classmethod
    def wrapLegend(cls, legend):
        return "\n  ".join(textwrap.wrap(legend, cls.LEGEND_WRAP_WIDTH))

    @classmethod
    def printTitle(cls, title, variables = None, filtering = None):
        return cls.wrapTitle(
            title.format(variables = variables if variables and len(variables) > 0 else "",
                         filtering = "with %s" % filtering if filtering is not None and len(filtering) > 0 else "")
        )

    @staticmethod
    def printParams(params, additionalString = None, removeZeros = True):
        out = []
        for k, v in params.iteritems():
            if type(v) in (tuple, list):
                o = repr(v)
            else:
                o = v
            if removeZeros and v:
                out.append("%s=%s" % (k.replace("MetricWeight", ""), o))
        s = ", ".join(out)
        if additionalString is not None and len(additionalString) > 0:
            s = ", ".join((s, additionalString)) if len(s) > 0 else additionalString
        return s

    @staticmethod
    def printVariables(variables, addiionalString = None):
        out = []
        for v in variables.keys():
            if type(v) in (tuple, list):
                o = repr(v)
            else:
                o = v
            out.append("%s" % o)
        s = ", ".join(out)
        if addiionalString is not None and len(addiionalString) > 0:
            s = ", ".join((s, addiionalString))
        return s


    @classmethod
    def _query(cls, x = None, y = None, parameters = None, filtering = None, distinct = False):
        #query db to get n-d array to plot
        query = cls.QueryBuilder('experiments')
        query.distinct = distinct
        # query.select(y)
        query.ands(x)
        query.ands(y)

        # for kx, condx in x.iteritems():
        #     query.where(kx, condx).cand()
        # query.closep().openp()
        query.ands(filtering)
        # for kg, condg in filtering.iteritems():
        #     query.where(kg, condg).cand()
        for kp, condp in parameters.iteritems():
            query.groupby(kp, condp)

        print(query.build())
        # print(db_read(query.build()))
        return query.getMap(), db_read(query.build())


    # @logGraph
    @classmethod
    def xy(cls, document = None, x = None, y = None, parameters = None, filtering = None):
        """
        format : {"var" : range} where range = [None | [min, max]]
        :param document:
        :param x: x value to graph
        :param y: y value to graph
        :param parameters: multiple graphs
        :param filtering: all graph must comply to filtering range
        :return:
        """
        #query db
        fig = cls.backend.newFigure()
        cmap, data = cls._query(x = x, y = y, parameters = parameters, filtering = filtering)
        data = np.transpose(np.array(data))
        for ax in x.iterkeys():
            # dt = Graph.sort(data, row = cmap[ax])
            if len(data) == 0:
                print "!!! No data found... skipping !!!\n"
                return

            # datax = dt[cmap[ax]]
            for ay in y.iterkeys():
                px, py, pstdy = cls.mergeAlong(data, rowalong = cmap[ax], what = cmap[ay])
                cls.backend.make(fig, px, py, yerr = pstdy, legend = cls.wrapLegend(ay))
                # cls.backend.make(fig, datax, data[cmap[ay]], legend = cls.wrapLegend(ay))
                cls.backend.decorate(g_xlabel = ax,
                                     g_ylabel = ay,
                                     g_ygrid = True,
                                     g_title = cls.printTitle("Sensitivity analysis of {variables} wrt %s {filtering}" % ax,
                                                              cls.printVariables(y),
                                                              cls.printParams(filtering)),
                                     )
            # cls.backend.setLegend()

        cls.backend.saveFigure(document, fig)

    @classmethod
    def mergeAlong(cls, data, rowalong, what):
        datax = data[rowalong]
        # from collections import OrderedDict
        tmpData = {}
        for i, x in np.ndenumerate(datax):
            if tmpData.has_key(x):
                tmpData[x].append(data[what][i])
            else:
                tmpData[x] = [data[what][i]]
        tmpx = np.array(tmpData.keys(), dtype=float)
        vals = [np.array(v, dtype = float) for v in tmpData.values()]
        tmpy = np.array([np.mean(v) for v in vals])
        tmpstd = np.array([np.std(v) for v in vals])
        d = Graph.sort(np.array([tmpx, tmpy, tmpstd]), row = 0)
        return d[0], d[1], d[2]

    @classmethod
    def cdfs(cls, document = None, x = None, y = None, parameters = None, filtering = None):
        """
        format : {"var" : range} where range = [None | [min, max]]
        :param document:
        :param x: x value to graph
        :param y: y value to graph
        :param parameters: multiple graphs
        :param filtering: all graph must comply to filtering range
        :return:
        """
        # query db
        cmap, d = cls._query(x = x, y = y, parameters = parameters, filtering = filtering, distinct = True)
        print d
        for ax in x.iterkeys():
            for ay in y.iterkeys():
                fig = cls.backend.newFigure()
                for res in d:
                    leg = str(res[cmap[ax]])
                    data = res[cmap[ay]]
                    if data is not None:
                        cls.backend.make(fig, x=data[0], y=data[1], legend = cls.wrapLegend(ax+"="+leg))
                cls.backend.decorate(g_xlabel = "",
                                     g_ylabel = "cdf",
                                     g_ygrid = True,
                                     g_title = cls.printTitle("Sensitivity analysis of {variables} wrt %s {filtering}" % ax,
                                                              ay,
                                                              cls.printParams(filtering)),
                                     )
                # cls.backend.setLegend()
                cls.backend.saveFigure(document, fig)


    @classmethod
    def sort(cls, array, row = 0):
        if array.size > 0:
            array = array[:, array[row].argsort()]
        return array

    def jitter(self, array):
        import numpy as np

        if array.size <= 1:
            return array
        maxJitter = (array.max() - array.min()) / 100.0
        # print array
        jit = (np.random.random_sample((array.size,)) - 0.5) * 2 * maxJitter
        # array += jit
        return array + jit

    @classmethod
    def speedAndAcc(cls, fi, x, filtering):
        Graph.xy(fi,
                 x = {x: None},
                 y = {exp_res_to_colname("speed", "avg", "avg"): None},
                 parameters = {},
                 filtering = filtering)

        # Graph().xy(fi,
        # x = {x : [0, 1]},
        #            y = {"speed_avg_avg" : None,
        #                 "speed_avg_std" : None},
        #            parameters = {},
        #            filtering = {})

        Graph.cdfs(fi,
                   x = {x: None},
                   y = {exp_res_to_colname("speed", "avg", "cdf"): None},
                   parameters = {},
                   filtering = filtering)

        Graph.cdfs(fi,
                   x = {x: None},
                   y = {exp_res_to_colname("acc", "cumulatedPlus", "cdf"): None,
                        exp_res_to_colname("acc", "cumulatedMinus", "cdf"): None},
                   parameters = {},
                   filtering = filtering)

    @classmethod
    def connections(cls, fi, x,filtering):
        Graph.xy(fi,
                 x = {x: None},
                 y = {exp_res_to_colname("agentInstConn", "avg", "avg"): None},
                 parameters = {},
                 filtering = filtering)

        Graph.cdfs(fi,
                   x = {x: None},
                   y = {exp_res_to_colname("agentInstConn", "avg", "cdf"): None},
                   parameters = {},
                   filtering = filtering)

        Graph.xy(fi,
                 x = {x: None},
                 y = {exp_res_to_colname("agentConn", "connect", "avg"): None},
                 parameters = {},
                 filtering = filtering)

        Graph.xy(fi,
                 x = {x: None},
                 y = {exp_res_to_colname("agentConn", "connect", "max"): None},
                 parameters = {},
                 filtering = filtering)

        Graph.xy(fi,
                 x = {x: None},
                 y = {exp_res_to_colname("roadConn", "connect", "sum"): None},
                 parameters = {},
                 filtering = filtering)

        Graph.cdfs(fi,
                   x = {x:None},
                   y = {exp_res_to_colname("timeAgentConn", "time_avg", "xy"): None},
                   parameters = {},
                   filtering = filtering)

        Graph.cdfs(fi,
                   x = {x: None},
                   y = {exp_res_to_colname("timeRoadConn", "time_avg", "xy"): None},
                   parameters = {},
                   filtering = filtering)


def makeGraphs(output_dir):
    import os.path as path

    speed = Graph.backend.newFile(path.join(output_dir, "speedFact.pdf"))
    Graph.speedAndAcc(speed, "roadsegments.trafficjam.speed-limit.factor",
                      {
                          # "roadsegments.trafficjam.speed-limit.factor" : 0.8,
                          "roadsegments.trafficjam.jamfactor" : 0.1,
                          "optimize.anticipation.position.seconds" : 1,
                          "agent.trafficjam.speed-limit.distance" : 1000
                      }
    )
    Graph.backend.close(speed)

    jamFact = Graph.backend.newFile(path.join(output_dir, "jamFactor.pdf"))
    Graph.speedAndAcc(jamFact, "roadsegments.trafficjam.jamfactor",
                      {
                          "roadsegments.trafficjam.speed-limit.factor": 0.8,
                          # "roadsegments.trafficjam.jamfactor": 0.1,
                          "optimize.anticipation.position.seconds": 1,
                          "agent.trafficjam.speed-limit.distance": 1000
                      }
    )
    Graph.backend.close(jamFact)

    distance = Graph.backend.newFile(path.join(output_dir, "distance.pdf"))
    Graph.speedAndAcc(distance, "roadsegments.trafficjam.speed-limit.distance",
                      {
                          "roadsegments.trafficjam.speed-limit.factor": 0.8,
                          "roadsegments.trafficjam.jamfactor": 0.1,
                          "optimize.anticipation.speed.seconds": 1,
                          # "agent.trafficjam.speed-limit.distance": 1000
                      }
    )
    Graph.backend.close(distance)

    anticipation = Graph.backend.newFile(path.join(output_dir, "anticipation.pdf"))
    Graph.connections(anticipation, "optimize.anticipation.position.seconds",
                      {
                          "roadsegments.trafficjam.speed-limit.factor": 0.8,
                          "roadsegments.trafficjam.jamfactor": 0.1,
                          # "optimize.anticipation.position.seconds": 1,
                          "agent.trafficjam.speed-limit.distance": 1000
                      }
    )
    Graph.backend.close(anticipation)


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

if __name__ == "__main__":
    ACTION_READ = "read"
    ACTION_WRITE = "write"
    ACTION_GRAPH = "graph"
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("--database", default = "sims.db")

    mode = parser.add_subparsers()
    write = mode.add_parser("write")
    write.set_defaults(action=ACTION_WRITE)
    write.add_argument("--output-dir", default = "output")
    write.add_argument("--parameters", default = "autotopo-config.properties")
    write.add_argument("--scenario", default = "scenario.xprj")

    read = mode.add_parser("read")
    read.set_defaults(action=ACTION_READ)
    read.add_argument("--shell", action = 'store_true', default = False)


    graph = mode.add_parser("graph")
    graph.set_defaults(action=ACTION_GRAPH)
    graph.add_argument("--output-dir", default = "graphs")



    opts = parser.parse_args()
    import sqlite3

    # Converts np.array to TEXT when inserting
    sqlite3.register_adapter(np.ndarray, adapt_array)

    # Converts TEXT to np.array when selecting
    sqlite3.register_converter(TypeHelper.CUSTOM_ARRAY, convert_array)

    connection = sqlite3.connect(opts.database, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

    if opts.action == ACTION_READ:
        SqliteShell(opts.database, connection).cmdloop()
    elif opts.action == ACTION_WRITE:
        db_prepare_base()

        params = getParameters(opts.parameters)
        data = getResults(opts.output_dir)
        scenario = getScenario(opts.scenario)
        res = makeResults(params, scenario, data)

        db_prepare_parameters(params)
        db_prepare_results(res)
        db_prepare_scenario(scenario)


        db_write_results(res)
    elif opts.action == ACTION_GRAPH:
        import os
        if not os.path.exists(opts.output_dir):
            os.mkdir(opts.output_dir)
        makeGraphs(opts.output_dir)


    connection.close()
