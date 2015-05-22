#!/usr/bin/python2.7
import sys
import os.path as path

sys.path.append(path.dirname(path.realpath(__file__)))

import csv
import numpy as np
from string import Template

from grapher import Graph
from storage import FileLock, Sqlite3, PandasCsv
from processing import FILE, TREATMENT, COLS, Function


RESULT_COLNAME_TPL = Template("${var}_${col}_${func}")

def exp_res_to_colname(var, col, func):
    return RESULT_COLNAME_TPL.substitute(var=var,
                                         col=col,
                                         func=func)

DATA_DESCRIPTION = {
    "speed": {
        FILE: "speed.csv",
        TREATMENT: [
            Function(("avg", "std", "cdf"), posparams="avg"),
        ],
    },
    "acc": {
        TREATMENT: [
            Function(("avg", "cdf"), posparams="cumulatedPlus"),
            Function(("avg", "cdf"), posparams="cumulatedMinus"),
        ],
        FILE: "acceleration.csv",
    },
    # "agentConn": {
    #     TREATMENT: [
    #         Function(("avg", "min", "max", "cdf"),
    #          posparams = Function("divide", kwparams={"num": "connect", "den": ("time", "time"), "nummap": "id", "denmap": ("time", "id")})
    #         )
    #     ],
    #     FILE: "agentConnections.csv",
    # },
    "agentInstConn": {
        TREATMENT: [
            Function(("avg", "cdf"), posparams="avg"),
            Function("max", posparams="max")
        ],
        FILE: "agentsInstantConnections.csv",
    },
    # "roadConn": {
    #     TREATMENT: [
    #         Function("sum", posparams="connect")
    #     ],
    #     FILE: "roadSegmentConnections.csv"
    # },
    # "roadInstConn": {
    #     TREATMENT: [
    #         Function("sum", posparams="avg")
    #     ],
    #     FILE: "roadSegmentInstantConnections.csv"
    # },
    "time": {
        TREATMENT: [
            Function(("avg", "cdf"), posparams="time")
        ],
        FILE: "time.csv"
    },
    "timeAgentConn": {
        TREATMENT: [
            Function(("avg", "cdf"), posparams="avg"),
            Function("xy", posparams=("time", "avg"))
        ],
        FILE: "timeAgentsInstantConnections.csv"
    },
    # "timeRoadConn": {
    #     TREATMENT: [
    #         Function(('avg', 'cdf'), posparams="avg"),
    #         Function("xy", posparams=("time", "avg"))
    #     ],
    #     FILE: "timeSegmentInstantConnections.csv"
    #
    # },
    # # "positions" : {
    # #     TREATMENT : [
    # #         ("xy", ('time', ('len', 'positions')))
    # #     ],
    # #     FILE : "positions.csv",
    # #     COLS : {"time":float,
    # #             "positions": ast.literal_eval}
    # # },
    # "numbers": {
    #     TREATMENT: [
    #         ("xy", ('time', 'number'))
    #     ],
    #     FILE: "numbers.csv"
    # },
    "scopes": {
        TREATMENT: [
            Function("avg", posparams = Function("minus", posparams= ("delete", "create"))),
            Function("cdf", posparams=
                Function("mul", posparams = (
                    Function("minus", posparams = ("delete", "create")),
                    "avg"
                )
            )
            ),
        ],
        FILE: "timeScope.csv"
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
            names = treatment.name()
            values = treatment.compute(data, name)
            # print names, values
            if type(names) is list:
                for i, n in enumerate(names):
                    dt[n] = values[i]
            else:
                dt[names] = values
    return dict(params.items() + dt.items() + scenario.items())


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

if __name__ == "__main__":

    # ACTION_READ = "read"
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

    # read = mode.add_parser("read")  #, parents=[parser])
    # read.set_defaults(action=ACTION_READ)
    # read.add_argument("--shell", action = 'store_true', default = False)
    # read.add_argument("--database", default="sims.db")

    graph = mode.add_parser("graph")  #, parents=[parser])
    graph.set_defaults(action=ACTION_GRAPH)
    graph.add_argument("--output-dir", default = "graphs")
    graph.add_argument("--database", default="sims.db")

    opts = parser.parse_args()
    p = PandasCsv(opts.database)
    # with Sqlite3(opts.database) as storage:
    with p as storage:
        # if opts.action == ACTION_READ:
        #     SqliteShell(opts.database, storage).cmdloop()
        if opts.action == ACTION_WRITE:
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
            makeGraphs(opts.output_dir)


## ## ## ## ## ## ## ##
# duree des connections / filtrage connexions courtes ?
# taux de connexion/deconnexion = nombre/duree de parcours ??
# taux de connexion road = nombre de connexion/nombre de voitures ???
# variables "adimentionnees"

# bursts avec taux d'injection voiture 0/1 + tester fonctionnement normal
# leader bias avec 0.1/0.5
# regarder taux de connection/nombre de connexions instantanees

# ============== #  /!\
# phase 1 => visualisation simplifiee (et comparaison ?)
# phase 2 => test grand nombres + variables interessante

# reprendre les scenarios + speed-diff faire 2x2 voies
# croiser les scenarios et les techniques


# objectifs => scenario classique ? (qu'est-ce que classique ???)


# motivations : routage + bouchon (si temps)


# ### look at rejection rates for merging.