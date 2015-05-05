__author__ = 'francois'

from string import Template
import numpy as np
import collections
import textwrap
import sqlite3

class _GnuplotGraph(type):

    class File(object):
        def __init__(self, path):
            self.path = path

    class Figure(object):

        def __init__(self):
            self.data = []

        def addData(self, d):
            self.data.append(d)

    def __new__(mcs, *args, **kwargs):
        # import Gnuplot
        import pyGnuplot
        import pyGnuplot.gpPlot_mod as fig
        import pyGnuplot.gpSinglePlot_mod as pl
        mcs.gp = pyGnuplot
        mcs.fig = fig
        mcs.pl = pl
        # mcs.gp.GnuplotOpts.default_term = 'pdf color'
        return type.__new__(mcs, *args, **kwargs)

    def newFigure(cls):
        return cls.fig.gpPlot(None)

    def decorate(cls, *args, **kwargs):
        pass

    def make(cls, figure, x, y, yerr = None, color = None, legend = None):
        # d = cls.gp.Data(x, y, title = legend)
        figure.add(cls.pl.gpSinglePlot(np.transpose([x, y]), rawdata=True))
        # if legend is not None:
        #     figure.gca().errorbar(x, y, yerr = yerr, color = color, label = legend)
        # else:
        #     figure.gca().errorbar(x, y, yerr = yerr)
        # cls.setMargins(figure.gca())
        # if x.size < 20:
        #     figure.gca().set_xticks(x)
        #     # cls.removeScale({}, x)

    def newFile(cls, path):
        g = cls.gp.gnuplot(debug=True)
        g.setTerm("pdf", enhanced=True,eps=True)
        g.output(path)
        g.cmd(g.output.set())
        return g
        # from matplotlib.backends.backend_pdf import PdfPages
        #
        # print('Creating new graph at %s\n' % path)
        # return PdfPages(path)

    @staticmethod
    def closePdf(pdf):
        # pdf.hardcopy(file="")
        # pdf('set output ""')
        pass
        # import datetime
        #
        # d = pdf.infodict()
        # d['Title'] = 'AutoTopo'
        # d['Author'] = u'Francois Espinet'
        # d['Subject'] = 'AutoTopo'
        # d['Keywords'] = 'autotopo'
        # d['ModDate'] = datetime.datetime.today()
        # pdf.close()
        # print("Graph successfully written\n\n")

    def saveFigure(cls, document, figure):
        document.show(figure)
        # for d in figure.data:
        #     document.plot(d)
        # figure("set terminal postscript")
        # # for ax in figure.get_axes():
        # # ax.set_position([0.1, 0.1, 0.5, 0.8])
        # document.savefig(figure, bbox_inches = 'tight', bbox_extra_artist = [cls.setLegend(figure)])
        # figure.clear()
        # cls.close(figure)

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

    def setLegend(cls, figure):
        from collections import OrderedDict

        handles, labels = figure.gca().get_legend_handles_labels()
        # merge identical labels
        by_label = OrderedDict(sorted(zip(labels, handles)))
        return figure.gca().legend(by_label.values(), by_label.keys(), loc = 'center left', bbox_to_anchor = (1, 0.5))
        # return figure.gca().legend(loc = 'center left', bbox_to_anchor = (1, 0.5))

    @staticmethod
    def setMargins(graph):
        margins = list(graph.margins())
        if margins[0] < 0.05:
            margins[0] = 0.05
        if margins[1] < 0.05:
            margins[1] = 0.05
        # self.gr.margins(x = 0.05, y = 0.05)
        graph.margins(*margins)

    def make(cls, figure, x, y, yerr = None, color = None, legend = None):
        if legend is not None:
            figure.gca().errorbar(x, y, yerr = yerr, color = color, label = cls.wrapLegend(legend))
        else:
            figure.gca().errorbar(x, y, yerr = yerr)
        cls.setMargins(figure.gca())
        if x.size < 20:
            figure.gca().set_xticks(x)
            # cls.removeScale({}, x)

    @staticmethod
    def newFile(path):
        from matplotlib.backends.backend_pdf import PdfPages

        print('Creating new graph at %s\n' % path)
        return PdfPages(path)

    @staticmethod
    def closePdf(pdf):
        import datetime

        d = pdf.infodict()
        d['Title'] = 'AutoTopo'
        d['Author'] = u'Francois Espinet'
        d['Subject'] = 'AutoTopo'
        d['Keywords'] = 'autotopo'
        d['ModDate'] = datetime.datetime.today()
        pdf.close()
        print("Graph successfully written\n\n")

    @classmethod
    def newFigure(cls):
        return cls.plt.figure()

    def saveFigure(cls, document, figure):
        # for ax in figure.get_axes():
        # ax.set_position([0.1, 0.1, 0.5, 0.8])
        document.savefig(figure, bbox_inches = 'tight', bbox_extra_artist = [cls.setLegend(figure)])
        figure.clear()
        cls.plt.close(figure)

    LEGEND_WRAP_WIDTH = 30

    def wrapLegend(cls, legend):
        return "\n  ".join(textwrap.wrap(legend, cls.LEGEND_WRAP_WIDTH))

class CsvBackend(object):
    pass

class GraphBackend(object):
    """Properties for making graphs and interface to graph object"""

    __metaclass__ = _PyplotGraph
    # __metaclass__ = _GnuplotGraph

    import random as rand

    colors = ['b', 'g', 'c', 'm', 'y', 'k',
              'blueviolet', 'brown', 'cadetblue', 'chartreuse', 'chocolate', 'coral', 'cornflowerblue', 'crimson',
              'darkblue', 'darkcyan', 'darkgrey', 'darkgreen', 'darkslateblue', 'darkgoldenrod', 'darkturquoise',
              'deeppink', 'dodgerblue', 'firebrick', 'forestgreen', 'fuchsia', 'green', 'greenyellow', 'hotpink',
              'indianred', 'indigo', 'lightseagreen', 'lightsalmon', 'limegreen', 'maroon', 'mediumaquamarine', 'mediumblue',
              'mediumvioletred', 'mediumslateblue', 'navy', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 'purple', 'royalblue',
              'seagreen', 'slateblue', 'sienna', 'steelblue', 'teal', 'tomato','aqua' ]
    # rand.shuffle(colors)
    markers = ['^', 'd', 'o', 'v', '>', '<', 'p', 's', '*']

    alpha = 0.9
    # alpha3d = 0.85
    # alphaSurf = 0.7

    # graphWidth = 10
    # _grHeight = 4
    # _titleHeight = 1.5

    @classmethod
    def getColor(cls, item, colDict):
        if not colDict.has_key(item):
            colDict[item] = cls.colors[len(colDict)%len(cls.colors)]
        return colDict[item]

    # @classmethod
    # def getColor(cls, item = None):
    #     """Get a color for item
    #     returns random color if item is none
    #     :param item: hash item to get color
    #     """
    #     if item is None or not isinstance(item, collections.Hashable):
    #         return cls.colors[cls.rand.randint(0, len(cls.colors) - 1)]
    #     return cls.colors[hash(item) % len(cls.colors)]

    @classmethod
    def getMarker(cls, item = None):
        if item is None or not isinstance(item, collections.Hashable):
            return cls.markers[cls.rand.randint(0, len(cls.markers) - 1)]
        return cls.markers[hash(item) % len(cls.markers)]

    # @classmethod
    # def graphHeight(cls, nGraphs = 1):
    #     return cls._grHeight * nGraphs + cls._titleHeight


    # @classmethod
    # def removeScale(cls, scaleDict, values):
    #     o = []
    #     for i, value in enumerate(values):
    #         if not scaleDict.has_key(value):
    #             scaleDict[value] = len(scaleDict) + 1
    #         o.append(scaleDict[value])
    #
    #     return o


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

FUNC="func"
NAME="name"

class Graph(object):
    backend = GraphBackend

    TITLE_WRAP_WIDTH = 60

    POST_FUNC = {
        "divide" : {
            FUNC: (np.divide, ['num', 'denom']),
            NAME: "{}/{}".format
        }
    }

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
        KW_LIKE = "LIKE"
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
            elif type(cond) in (basestring, str):
                self._select_where.extend((self.LP, qwhat, self.KW_LIKE, self.quote(cond), self.RP))
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


    def __init__(self, db):
        self.db = db

    @classmethod
    def wrapTitle(cls, title):
        return "\n".join(textwrap.wrap(title, cls.TITLE_WRAP_WIDTH))


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

    def _query(self, x = None, y = None, parameters = None, filtering = None, distinct = False):
        # query db to get n-d array to plot
        query = self.QueryBuilder('experiments')
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
        return query.getMap(), self.db.read(query.build())

    def _extract_treatements(self, variable):
        r = []
        for v in variable.iterkeys():
            if self.POST_FUNC.has_key(v):
                r.append(self.POST_FUNC[v])
        return r

    def _extract_cols(self, variable):
        # "divide":{
        #     "num": {exp_res_to_colname("agentInstConn", "avg", "avg"): None},
        #     "denom": {exp_res_to_colname("roadInstConn", "avg", "avg"): None}
        # }
        r = {}
        for v in variable.iterkeys():
            # if given a function instead of simple column
            if v in self.POST_FUNC:
                f, args = self.POST_FUNC[v][FUNC]
                for a in args:
                    r.update(variable[v][a])
            else:
                r[v] = variable[v]
        return r

    def apply_post_treatments(self, data, cmap, x, y):
        cmap, data, nx = self._apply_post_treatement(data, cmap, x)
        cmap, data, ny = self._apply_post_treatement(data, cmap, y)
        return cmap, data, nx, ny

    def _apply_post_treatement(self, data, cmap, variable):
        nv = {}
        newd = []
        for v in variable.iterkeys():
            if v in self.POST_FUNC:
                f, args = self.POST_FUNC[v][FUNC]
                argcols = []
                argscolsname = []
                for a in args:
                    colname = variable[v][a].keys()[0]
                    argcols.append(np.array(data[cmap[colname]], dtype=float))
                    argscolsname.append(colname)
                newd.append(f(*argcols))
                funcname = self.POST_FUNC[v][NAME](*argscolsname)
                cmap[funcname] = len(cmap)
                nv[funcname] = None
            else :
                nv[v] = variable[v]
        if len(newd) >0:
            data = np.append(data, np.array(newd), axis=0)
        return cmap, data, nv

    # @logGraph
    def xy(self, document = None, x = None, y = None, parameters = None, filtering = None):
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
        fig = self.backend.newFigure()
        cmap, data = self._query(x = self._extract_cols(x), y = self._extract_cols(y), parameters = parameters, filtering = filtering)
        data = np.transpose(np.array(data))
        cmap, data, x, y = self.apply_post_treatments(data, cmap, x, y)
        print "Plotting data..."
        for ax in x.iterkeys():
            # dt = Graph.sort(data, row = cmap[ax])
            if len(data) == 0:
                print "!!! No data found... skipping !!!\n"
                return

            # datax = dt[cmap[ax]]
            colDict = {}
            for ay in y.iterkeys():
                px, py, pstdy = self.mergeAlong(data, rowalong = cmap[ax], what = cmap[ay])
                self.backend.make(fig, px, py, yerr = pstdy, color = self.backend.getColor(ay, colDict),legend = ay)
                # cls.backend.make(fig, datax, data[cmap[ay]], legend = cls.wrapLegend(ay))
                self.backend.decorate(g_xlabel = ax,
                                     g_ylabel = ay,
                                     g_ygrid = True,
                                     g_title = self.printTitle("Sensitivity analysis of {variables} wrt %s {filtering}" % ax,
                                                              self.printVariables(y),
                                                              self.printParams(filtering)),
                                     )
            # cls.backend.setLegend()

        self.backend.saveFigure(document, fig)
        print "Done"

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

    def cdfs(self, document = None, x = None, y = None, parameters = None, filtering = None):
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
        cmap, d = self._query(x = x, y = y, parameters = parameters, filtering = filtering, distinct = True)
        # print d
        print "Plotting data..."
        for ax in x.iterkeys():
            for ay in y.iterkeys():
                fig = self.backend.newFigure()
                colDict = {}
                for res in d:
                    leg = str(res[cmap[ax]])
                    data = res[cmap[ay]]
                    if data is not None:
                        self.backend.make(fig, x=data[0], y=data[1], color = self.backend.getColor(leg, colDict),legend = ax+"="+leg)
                self.backend.decorate(g_xlabel = "",
                                     g_ylabel = "cdf",
                                     g_ygrid = True,
                                     g_title = self.printTitle("Sensitivity analysis of {variables} wrt %s {filtering}" % ax,
                                                              ay,
                                                              self.printParams(filtering)),
                                     )
                # self.backend.setLegend()
                self.backend.saveFigure(document, fig)
        print "Done"

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