#!/usr/bin/python2.7
import sys
import os.path as path

sys.path.append(path.dirname(path.realpath(__file__)))

import csv
import numpy as np
from string import Template

from grapher import Graph
from storage import Sqlite3, FileLock, TypeHelper

RESULT_COLNAME_TPL = Template("${var}_${col}_${func}")


def exp_res_to_colname(var, col, func):
    return RESULT_COLNAME_TPL.substitute(var=var,
                                         col=col,
                                         func=func)


HIST_PARAMS = {
    'min': 0,
    'max': 20,
    'nbins': 12
}

import ast

TREATMENT = "treatment"
FILE = "file"
COLS = "columns"
# treatment format : {var/file : [(funcs)|func, col|(func)]}
DATA_DESCRIPTION = {
    "speed": {
        FILE: "speed.csv",
        TREATMENT: [
            (("avg", "std", "cdf"), "avg"),
        ],
    },
    "acc": {
        TREATMENT: [
            (("avg", "cdf"), "cumulatedPlus"),
            (("avg", "cdf"), "cumulatedMinus"),
        ],
        FILE: "acceleration.csv",
    },
    "agentConn": {
        TREATMENT: [
            (("avg", "min", "max", "cdf"),
             ("divide", {"num": "connect", "den": ("time", "time"), "nummap": "id", "denmap": ("time", "id")}))
        ],
        FILE: "agentConnections.csv",
    },
    "agentInstConn": {
        TREATMENT: [
            (("avg", "cdf"), "avg"),
            ("max", "max")
        ],
        FILE: "agentsInstantConnections.csv",
    },
    "roadConn": {
        TREATMENT: [
            ("sum", "connect")
        ],
        FILE: "roadSegmentConnections.csv"
    },
    "roadInstConn": {
        TREATMENT: [
            ("sum", "avg")
        ],
        FILE: "roadSegmentInstantConnections.csv"
    },
    "time": {
        TREATMENT: [
            (("avg", "cdf"), "time")
        ],
        FILE: "time.csv"
    },
    "timeAgentConn": {
        TREATMENT: [
            (("avg", "cdf"), "avg"),
            ("xy", ("time", "avg"))
        ],
        FILE: "timeAgentsInstantConnections.csv"
    },
    "timeRoadConn": {
        TREATMENT: [
            (('avg', 'cdf'), "avg"),
            ("xy", ("time", "avg"))
        ],
        FILE: "timeSegmentInstantConnections.csv"

    },
    # "positions" : {
    #     TREATMENT : [
    #         ("xy", ('time', ('len', 'positions')))
    #     ],
    #     FILE : "positions.csv",
    #     COLS : {"time":float,
    #             "positions": ast.literal_eval}
    # },
    "numbers": {
        TREATMENT: [
            ("xy", ('time', 'number'))
        ],
        FILE: "numbers.csv"
    }
}


class CsvReader():
    def __init__(self, file, cols=None):
        """
        use cols for checking ?
        :param file:
        :param cols:
        :return:
        """
        # self.cols = {col:i for i, col in enumerate(cols)}
        with open(file, 'r') as f:
            reader = csv.reader(f, delimiter=";", quotechar='"')
            self.cols = {col: i for i, col in enumerate(reader.next())}

            if cols is not None:
                import operator

                r = []
                for row in reader:
                    e = []
                    for col, i in sorted(self.cols.items(), key=operator.itemgetter(1)):
                        if cols.has_key(col):
                            treat = cols[col]
                            e.append(treat(row[i]))
                        else:
                            e.append(row[i])
                    r.append(e)
            else:
                r = [row for row in reader]

            self.data = np.array(r, dtype=float)

    def _colToNum(self, col):
        return self.cols[col]

    def getColumn(self, col):
        return self.data[:, self._colToNum(col)]

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
    def xy(cls, x, y):
        return cls.np.array([x, y])

    @classmethod
    def divide(cls, num=None, den=None, nummap=None, denmap=None):
        if nummap is None or denmap is None:
            return cls.np.divide(num, den)
        dden = {denmap[i]: val for i, val in enumerate(den)}
        aden = []
        for i, val in enumerate(num):
            aden.append(dden[nummap[i]])
        return cls.np.divide(num, aden)

    @classmethod
    def getPrintableName(cls, func, *args, **kwargs):
        f = cls.NAME_MAPPING.get(func, cls.DEFAULT_NAME_MAPPING)
        return f.format(*args, func=func, **kwargs)

    DEFAULT_NAME_MAPPING = "{func}({})"

    NAME_MAPPING = {
        "divide": "{num}/{den}",
        "xy": "{},{}"
    }

    FUNC_MAP = {
        "avg": np.average,
        "min": np.min,
        "max": np.max,
        "hist": hist,
        "sum": np.sum,
        "cdf": cdf,
        "std": np.std,
        "xy": xy,
        "divide": divide,
        "len": len,
    }

    def __getattr__(cls, item):
        return cls.FUNC_MAP[item]


class FuncHelper(object):
    """Properties for making graphs and interface to graph object"""
    __metaclass__ = _FuncHelper


def readResults(dir):
    data = {}
    # load data from files
    for name, desc in DATA_DESCRIPTION.iteritems():
        data[name] = CsvReader(path.join(dir, desc[FILE]), desc[COLS] if desc.has_key(COLS) else None)  # ,desc[COLS]

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

    out = {"scenario": scenario}
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
        qs = np.array(qs, dtype=float).transpose()
        out['inflow_speed_%s' % roadid] = vs
        out['inflow_q_%s' % roadid] = qs
        meanqval.append(np.trapz(y=qs[1], x=qs[0]))
        meanqw.append(qs[0].max() - qs[0].min())
        meanspeedval.append(np.trapz(y=vs[1], x=vs[0]))
        meanspeedw.append(vs[0].max() - vs[0].min())
    # print meanflow
    out['inflow_mean_speed'] = np.average(meanspeedval, weights=meanspeedw) / np.mean(meanspeedw)
    out['inflow_mean_q'] = np.average(meanqval, weights=meanqw) / np.mean(meanqw)

    return out


def crunchResults(params, scenario, data):
    dt = {}
    # leave params as is
    for name, values in data.iteritems():
        for treatment in DATA_DESCRIPTION[name][TREATMENT]:
            funcs, args = splitTuple(treatment)
            displayargs = printableArgs(args)
            args, kwargs = reduceArgs(args, data, name)

            # run each func with given args (r)
            if type(funcs) in (tuple, list):
                for func in funcs:
                    dt[exp_res_to_colname(name, displayargs, func)] = getattr(FuncHelper, func)(*args, **kwargs)
            else:
                dt[exp_res_to_colname(name, displayargs, funcs)] = getattr(FuncHelper, funcs)(*args, **kwargs)

    # print dt
    return dict(params.items() + dt.items() + scenario.items())


def printableArgs(oargs, func=None):
    out = ""
    if type(oargs) in (tuple, list):
        if oargs[0] in FuncHelper.FUNC_MAP:
            out += printableArgs(splitTuple(oargs)[1], func=oargs[0])
        else:
            out += "_".join(oargs)
    elif type(oargs) is dict:
        out += FuncHelper.getPrintableName(func, **{k: printableArgs(v) for k, v in oargs.iteritems()})
    else:
        out += oargs

    return out


def reduceArgs(oargs, data, curname):
    kwargs = {}
    args = ()
    # 1 ("renorm", {"x":"connect", "y": ("time", "avg"), "xmap":"id", "ymap":("time", "id")}))
    # 2 ("func", ("posarg1", "posarg2")
    # 3 ("col1", "col2")
    # 4 "col"
    if type(oargs) in (tuple, list):
        if oargs[0] in FuncHelper.FUNC_MAP:
            split = splitTuple(oargs)
            # nested functions
            aargs, akwargs = reduceArgs(split[1], data, curname)
            args = (getattr(FuncHelper, split[0])(*aargs, **akwargs),)
        else:
            # 3
            args = tuple(data[curname].getColumn(a) for a in oargs)
    elif type(oargs) is dict:
        for k, v in oargs.iteritems():
            if type(v) in (tuple, list):
                name, col = v
            else:
                name = curname
                col = v

            kwargs[k] = data[name].getColumn(col)
    else:
        # 4
        args = (data[curname].getColumn(oargs),)

    return args, kwargs


def splitTuple(t):
    ne = t[1:]
    if len(ne) == 1:
        ne = ne[0]

    return t[0], ne


import cmd


class SqliteShell(cmd.Cmd):
    PROMPT = "Sqlite (%s) > "
    OUT = ">> %s"

    def __init__(self, database, db):
        cmd.Cmd.__init__(self)
        self.prompt = self.PROMPT % database
        self.db = db

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

    def sql(self, arg):
        if arg is not None:
            try:
                print self.OUT % repr(self.db.read(arg))
            except sqlite3.Error as e:
                print e.message

    def disp_data(self, arg):
        print self.db.table_info("experiments")
        print self.db.table_content("experiments")


def speedAndAcc(fi, x, filtering):
    thegraph.xy(fi,
                x={x: None},
                y={exp_res_to_colname("speed", "avg", "avg"): None},
                parameters={},
                filtering=filtering)

    thegraph.cdfs(fi,
                  x={x: None},
                  y={exp_res_to_colname("speed", "avg", "cdf"): None},
                  parameters={},
                  filtering=filtering)

    thegraph.cdfs(fi,
                  x={x: None},
                  y={exp_res_to_colname("acc", "cumulatedPlus", "cdf"): None,
                     exp_res_to_colname("acc", "cumulatedMinus", "cdf"): None},
                  parameters={},
                  filtering=filtering)


def connections(fi, x, filtering):
    thegraph.xy(fi,
                x={x: None},
                y={exp_res_to_colname("agentInstConn", "avg", "avg"): None},
                parameters={},
                filtering=filtering)

    thegraph.cdfs(fi,
                  x={x: None},
                  y={exp_res_to_colname("agentInstConn", "avg", "cdf"): None},
                  parameters={},
                  filtering=filtering)

    thegraph.xy(fi,
                x={x: None},
                y={exp_res_to_colname("roadInstConn", "avg", "sum"): None},
                parameters={},
                filtering=filtering)

    thegraph.xy(fi,
                x={x: None},
                y={"agentConn_connect/time_time_avg": None},
                parameters={},
                filtering=filtering)

    thegraph.xy(fi,
                x={x: None},
                y={exp_res_to_colname("roadConn", "connect", "sum"): None},
                parameters={},
                filtering=filtering)

    thegraph.xy(fi,
                x={x: None},
                y={
                    "divide": {
                        "num": {exp_res_to_colname("agentInstConn", "avg", "avg"): None},
                        "denom": {exp_res_to_colname("roadConn", "connect", "sum"): None}
                    }
                },
                parameters={},
                filtering=filtering
                )

    thegraph.xy(fi,
                x={x: None},
                y={
                    "divide": {
                        "num": {exp_res_to_colname("roadInstConn", "avg", "sum"): None},
                        "denom": {exp_res_to_colname("roadConn", "connect", "sum"): None}
                    }
                },
                parameters={},
                filtering=filtering
                )

    thegraph.cdfs(fi,
                  x={x: None},
                  y={exp_res_to_colname("timeAgentConn", "time_avg", "xy"): None},
                  parameters={},
                  filtering=filtering)

    thegraph.cdfs(fi,
                  x={x: None},
                  y={exp_res_to_colname("timeRoadConn", "time_avg", "xy"): None},
                  parameters={},
                  filtering=filtering)


def makeSpeedGraph(output_dir):
    speed = thegraph.backend.newFile(path.join(output_dir, "speedFact.pdf"))
    speedAndAcc(speed, "roadsegments.trafficjam.speed-limit.factor",
                {
                    "roadsegments.trafficjam.enabled": "true",
                    "roadsegments.trafficjam.interjamdistance": 1000,
                    "roadsegments.trafficjam.jamfactor": 0.1,

                    "agent.trafficjam.speed-limit.distance": 1000,

                    "optimize.agent.recenter-leader.enabled": "false",
                    "optimize.roadsegment.speed-clustering.enabled": "false",

                }
                )
    thegraph.backend.closePdf(speed)


def makeJamGraph(output_dir):
    jamFact = thegraph.backend.newFile(path.join(output_dir, "jamFactor.pdf"))
    speedAndAcc(jamFact, "roadsegments.trafficjam.jamfactor",
                {
                    "roadsegments.trafficjam.enabled": "true",
                    "roadsegments.trafficjam.interjamdistance": 1000,
                    "roadsegments.trafficjam.speed-limit.factor": 0.8,

                    "agent.trafficjam.speed-limit.distance": 1000,
                    "optimize.agent.recenter-leader.enabled": "false",
                    "optimize.roadsegment.speed-clustering.enabled": "false",
                }
                )
    thegraph.backend.closePdf(jamFact)


def makeDistanceGraph(output_dir):
    distance = thegraph.backend.newFile(path.join(output_dir, "distance.pdf"))
    speedAndAcc(distance, "agent.trafficjam.speed-limit.distance",
                {
                    "roadsegments.trafficjam.enabled": "true",
                    "roadsegments.trafficjam.interjamdistance": 1000,
                    "roadsegments.trafficjam.speed-limit.factor": 0.8,
                    "roadsegments.trafficjam.jamfactor": 0.1,

                    "optimize.agent.recenter-leader.enabled": "false",
                    "optimize.roadsegment.speed-clustering.enabled": "false",
                }
                )
    thegraph.backend.closePdf(distance)


def makeAnticipationGraph(output_dir):
    anticipation = thegraph.backend.newFile(path.join(output_dir, "anticipation.pdf"))
    connections(anticipation, "optimize.anticipation.position.seconds",
                {
                    "roadsegments.trafficjam.enabled": "false",
                    "optimize.agent.recenter-leader.enabled": "false",
                    "optimize.roadsegment.speed-clustering.enabled": "false",
                }
                )
    thegraph.backend.closePdf(anticipation)


def makeSpeedClusteringGraph(output_dir):
    speedClustering = thegraph.backend.newFile(path.join(output_dir, "speed_clustering.pdf"))
    connections(speedClustering, "optimize.roadsegment.speed-clustering.factor",
                {
                    "roadsegments.trafficjam.enabled": "false",
                    "optimize.agent.recenter-leader.enabled": "false",
                    "optimize.roadsegment.speed-clustering.enabled": "true",
                    "optimize.anticipation.position.seconds": 0
                }
                )
    thegraph.backend.closePdf(speedClustering)


def makeRecenterLeaderGraph(output_dir):
    recenterLeader = thegraph.backend.newFile(path.join(output_dir, "recenter_leader.pdf"))
    connections(recenterLeader, "optimize.agent.recenter-leader.period",
                {
                    "roadsegments.trafficjam.enabled": "false",
                    "optimize.agent.recenter-leader.enabled": "true",
                    "optimize.roadsegment.speed-clustering.enabled": "false",
                    # "optimize.agent.recenter-leader.period": 3,
                    "optimize.agent.recenter-leader.bias": 2,
                }
                )

    connections(recenterLeader, "optimize.agent.recenter-leader.bias",
                {
                    "roadsegments.trafficjam.enabled": "false",
                    "optimize.agent.recenter-leader.enabled": "true",
                    "optimize.roadsegment.speed-clustering.enabled": "false",
                    "optimize.agent.recenter-leader.period": 3,
                    # "optimize.agent.recenter-leader.bias": 2,
                }
                )
    thegraph.backend.closePdf(recenterLeader)


def makeGraphs(output_dir):
    # #### Traffic jams
    # {
    #     "roadsegments.trafficjam.enabled" : False,
    #     "roadsegments.trafficjam.interjamdistance" : 1000,
    #     "roadsegments.trafficjam.jamfactor" : 0.1,
    #     "roadsegments.trafficjam.speed-limit.factor" : 0.8,
    #     "agent.trafficjam.speed-limit.distance" : 1000,
    #
    #     ##### Topology optimizations
    #     "optimize.agent.recenter-leader.enabled" : False,
    #     "optimize.agent.recenter-leader.period" : 3,
    #     "optimize.agent.recenter-leader.bias" : 2,
    #
    #     "optimize.roadsegment.speed-clustering.enabled" : False,
    #     "optimize.roadsegment.speed-clustering.factor" : 0,
    #
    #     #use 0 to deactivate
    #     "optimize.anticipation.position.seconds" : 0,
    #
    #     "speed.limit.default" : 15
    # }
    # {
    #     "roadsegments.trafficjam.enabled": False,
    #     "optimize.agent.recenter-leader.enabled": False,
    #     "optimize.roadsegment.speed-clustering.enabled": False,
    #
    #     "roadsegments.trafficjam.interjamdistance": 1000,
    #     "roadsegments.trafficjam.jamfactor": 0.1,
    #     "roadsegments.trafficjam.speed-limit.factor": 0.8,
    #
    #     "agent.trafficjam.speed-limit.distance": 1000,
    #
    #     # #### Topology optimizations
    #     "optimize.agent.recenter-leader.period": 3,
    #     "optimize.agent.recenter-leader.bias": 2,
    #     "optimize.roadsegment.speed-clustering.factor": 0,
    #     #use 0 to deactivate
    #     "optimize.anticipation.position.seconds": 0,
    # }
    # import multiprocessing as mp
    # p = mp.Pool(8)
    # p.apply_async(makeSpeedGraph, [output_dir])
    # p.apply_async(makeSpeedClusteringGraph, [output_dir])
    # p.apply_async(makeJamGraph, [output_dir])
    # p.apply_async(makeDistanceGraph, [output_dir])
    # p.apply_async(makeAnticipationGraph, [output_dir])
    # p.apply_async(makeRecenterLeaderGraph, [output_dir])
    # p.close()
    # p.join()

    makeSpeedGraph(output_dir)
    makeSpeedClusteringGraph(output_dir)
    makeJamGraph(output_dir)
    makeDistanceGraph(output_dir)
    makeAnticipationGraph(output_dir)
    makeRecenterLeaderGraph(output_dir)


import sqlite3
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

    mode = parser.add_subparsers()
    write = mode.add_parser("write")  # , parents=[parser])
    write.set_defaults(action=ACTION_WRITE)
    write.add_argument("--output-dir", default = "output")
    write.add_argument("--parameters", default = "autotopo-config.properties")
    write.add_argument("--scenario", default = "scenario.xprj")

    write.add_argument("--database", default="sims.db")

    read = mode.add_parser("read")  #, parents=[parser])
    read.set_defaults(action=ACTION_READ)
    read.add_argument("--shell", action = 'store_true', default = False)
    read.add_argument("--database", default="sims.db")

    graph = mode.add_parser("graph")  #, parents=[parser])
    graph.set_defaults(action=ACTION_GRAPH)
    graph.add_argument("--output-dir", default = "graphs")
    graph.add_argument("--database", default="sims.db")

    opts = parser.parse_args()

    # Converts np.array to TEXT when inserting
    sqlite3.register_adapter(np.ndarray, adapt_array)

    # Converts TEXT to np.array when selecting
    sqlite3.register_converter(TypeHelper.CUSTOM_ARRAY, convert_array)

    with Sqlite3(
            sqlite3.connect(opts.database, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)) as storage:
        if opts.action == ACTION_READ:
            SqliteShell(opts.database, storage).cmdloop()
        elif opts.action == ACTION_WRITE:
            with FileLock(path.join(path.dirname(path.realpath(__file__)), ".db_lock")) as lock:
                print "Recording results into database"
                storage.prepare()

                params = getParameters(opts.parameters)
                data = readResults(opts.output_dir)
                scenario = getScenario(opts.scenario)
                res = crunchResults(params, scenario, data)

                storage.write_row(res)
                print "Results recorded"
        elif opts.action == ACTION_GRAPH:
            if not path.exists(opts.output_dir):
                from os import mkdir

                mkdir(opts.output_dir)
            thegraph = Graph(storage)
            print thegraph.db
            makeGraphs(opts.output_dir)


##
# duree des connections / filtrage connexions courtes ?
# taux de connexion/deconnexion = nombre/duree de parcours ??
# taux de connexion road = nombre de connexion/nombre de voitures ???
# variables "adimentionnees"
