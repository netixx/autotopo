#!/usr/bin/python2.7
import sys
import os.path as path

sys.path.append(path.dirname(path.realpath(__file__)))

import csv
import numpy as np
from string import Template

from grapher import PandasGraph as Graph
from storage import FileLock, Sqlite3, PandasCsv, PandasPickle, PandasJson, PandasHDF, RawStorage, ProcessedStorage, Zip
from processing import FILE, TREATMENT, COLS, Function, Fetch, PostFunction
from collections import OrderedDict

DATA_DESCRIPTION = OrderedDict([
    ("speed", {
        FILE: "speed.csv",
        TREATMENT: [
            Function(("avg", "std", "cdf"), posparams="avg"),
        ],
    }),
    ("acc", {
        TREATMENT: [
            Function(("avg", "cdf"), posparams="cumulatedPlus"),
            Function(("avg", "cdf"), posparams="cumulatedMinus"),
        ],
        FILE: "acceleration.csv",
    }),
    ("time", {
        TREATMENT: [
            Function(("avg", "cdf"), posparams="time")
        ],
        FILE: "time.csv"
    }),
    ("numbers", {
        TREATMENT: [Function("xy", posparams=("time", "number"))],
        FILE:"numbers.csv"
    }),
    ("timeRoadConn", {
        TREATMENT: [
            # Function(('avg', 'cdf'), posparams="avg"),
            Function("xy", posparams=("time", Function("divide",
                                                       kwparams={"num" : "avg", "den" : Fetch("numbers", "number"),
                                                                 "nummap" : "time", "denmap" : Fetch("numbers", "time")})))
        ],
        FILE: "timeSegmentInstantConnections.csv"
    }),
    ("agentConn", {
        TREATMENT: [
            Function(("avg", "max", "cdf"),
             posparams = Function("divide", kwparams={"num": "connect", "den": Fetch("time", "time"), "nummap": "id", "denmap": Fetch("time", "id")})
            )
        ],
        FILE: "agentConnections.csv",
    }),
    ("roadConn", {
        TREATMENT: [
            Function("sum", posparams= Function("divide", kwparams={"num" : "connect", "den" : Function("len", posparams=Fetch("agentConn", "id"))}))
        ],
        FILE: "roadSegmentConnections.csv"
    }),
    ("agentInstConn", {
        TREATMENT: [
            Function(("avg", "cdf"), posparams = "avg"),
            # Function("max", posparams = "max")
        ],
        FILE: "agentsInstantConnections.csv",
    }),
    ("roadInstConn", {
        TREATMENT: [
            Function("sum", posparams = "avg")
        ],
        FILE: "roadSegmentInstantConnections.csv"
    }),
    ("timeAgentConn", {
        TREATMENT: [
            Function(("avg", "cdf"), posparams="avg"),
            # Function("xy", posparams=("time", "avg"))
        ],
        FILE: "timeAgentsInstantConnections.csv"
    }),
    ("scopes", {
        TREATMENT: [
            Function(("cdf", "avg"), posparams = Function("minus", posparams = ("delete", "create"))),
            Function(("cdf", "avg"), posparams = Function("mul", posparams = (
                Function("minus", posparams = ("delete", "create")),
                "avg"
            )
            )
            ),
            Function("cdf", posparams="avg")
        ],
        FILE: "timeScope.csv"
    })
])

import pandas as pd
class PandasCsvReader(object):
    def __init__(self, file, cols=None):
        self.data = pd.read_csv(file, sep=";", quotechar='"', dtype=np.float)


    def getColumn(self, col):
        return self.data[col]


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


def getScenario(scenario, root):
    from xml.dom import minidom

    out = {"scenario": os.path.relpath(scenario, root)}
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
    out['inflow_mean_speed'] = np.average(meanspeedval, weights=meanspeedw) / np.mean(meanspeedw)
    out['inflow_mean_q'] = np.average(meanqval, weights=meanqw) / np.mean(meanqw)

    return out

COL_TPL=Template("${name}_${treat}")

def crunchResults(params, scenario, data):
    dt = {}
    # leave params as is
    for name, values in data.iteritems():
        if DATA_DESCRIPTION[name].has_key(TREATMENT):
            for treatment in DATA_DESCRIPTION[name][TREATMENT]:
                names = treatment.name()
                values = treatment.compute(data, name)
                # print names, values
                if type(names) is list:
                    for i, n in enumerate(names):
                        col = COL_TPL.substitute(name=name, treat=n)
                        dt[col] = values[i]
                else:
                    col = COL_TPL.substitute(name=name, treat=names)
                    dt[col] = values
    return dict(params.items() + dt.items() + scenario.items())

# def compareConfig(output_dir, graph):
#     defaultBias = 0
#     defaultPeriod = 0
#     defaultSpeedClust = 0
#     defaults = {
#         "optimize.agent.recenter-leader.enabled": 'false',
#         "optimize.roadsegment.speed-clustering.enabled": 'false',
#         "roadsegments.trafficjam.enabled": 'false',
#         "optimize.anticipation.position.seconds": 0
#     }
#
#     recenterLeaderPeriod = graph.backend.newDocument(path.join(output_dir, "recenter_leader_period.pdf"))
#
#     graph.xy(recenterLeaderPeriod,
#              x = {"optimize.agent.recenter-leader.period": None},
#              y = {"scopes_avg((delete-create)*avg)": None},
#              parameters = {"agent.connections.distance.max": None},
#              filtering = {"optimize.agent.recenter-leader.enabled": 'true',
#                           "optimize.roadsegment.speed-clustering.enabled": 'false',
#                           "optimize.agent.recenter-leader.bias": defaultBias
#              },
#              default = defaults
#     )
#
#     graph.backend.closeDocument(recenterLeaderPeriod)


def makeGraphs(output_dir, graph):
    defaultBias = 0
    defaultPeriod = 0
    defaultSpeedClust = 0
    defaults = {
        "optimize.agent.recenter-leader.enabled": 'false',
        "optimize.roadsegment.speed-clustering.enabled": 'false',
        "roadsegments.trafficjam.enabled": 'false',
        "optimize.anticipation.position.seconds" : 0
    }
    recenterLeaderBias = graph.backend.newDocument(path.join(output_dir, "recenter_leader_bias"))
    graph.xy(recenterLeaderBias,
             x = {"optimize.agent.recenter-leader.bias": None},
             y = {"scopes_avg((delete-create))" : None},
             parameters = {"scenario" : None},
             filtering= {"optimize.agent.recenter-leader.enabled" : 'true',
                         "optimize.roadsegment.speed-clustering.enabled": 'false',
                         "optimize.agent.recenter-leader.period" : defaultPeriod
             },
             default = defaults
    )

    graph.xy(recenterLeaderBias,
             x = {"optimize.agent.recenter-leader.bias": None},
             y = {"scopes_avg((delete-create)*avg)": None},
             parameters = {"scenario": None},
             filtering = {"optimize.agent.recenter-leader.enabled": 'true',
                          "optimize.roadsegment.speed-clustering.enabled": 'false',
                          "optimize.agent.recenter-leader.period": defaultPeriod
             },
             default = defaults
    )

    graph.xy(recenterLeaderBias,
             x = {"optimize.agent.recenter-leader.bias": None},
             y = {"roadConn_sum(connect/len(agentConn(id)))": None},
             parameters = {"scenario": None},
             filtering = {"optimize.agent.recenter-leader.enabled": 'true',
                          "optimize.roadsegment.speed-clustering.enabled": 'false',
                          "optimize.agent.recenter-leader.period": defaultPeriod
             },
             default = defaults
    )

    graph.xycompare(recenterLeaderBias,
               xy = {"scopes_cdf((delete-create)*avg)" : None},
               parameters = {"optimize.agent.recenter-leader.bias": None},
               filtering = {"optimize.agent.recenter-leader.enabled": 'true',
                            "optimize.roadsegment.speed-clustering.enabled": 'false',
                            "scenario" : "large-10.xprj",
                            "optimize.agent.recenter-leader.period": defaultPeriod
               },
               default = defaults
    )

    graph.xycompare(recenterLeaderBias,
                    xy = {"scopes_cdf((delete-create)*avg)": None},
                    parameters = {"scenario" : None},
                    filtering = {"optimize.agent.recenter-leader.enabled": 'true',
                                 "optimize.agent.recenter-leader.bias": defaultBias,
                                 "optimize.roadsegment.speed-clustering.enabled": 'false'
                    },
                    default = defaults
    )

    graph.backend.closeDocument(recenterLeaderBias)

    recenterLeaderPeriod = graph.backend.newDocument(path.join(output_dir, "recenter_leader_period"))

    graph.xy(recenterLeaderPeriod,
             x = {"optimize.agent.recenter-leader.period": None},
             y = {"scopes_avg((delete-create))": None},
             parameters = {"scenario": None},
             filtering = {"optimize.agent.recenter-leader.enabled": 'true',
                          "optimize.roadsegment.speed-clustering.enabled": 'false',
                          "optimize.agent.recenter-leader.bias" : defaultBias
             },
             default = defaults
    )

    graph.xy(recenterLeaderPeriod,
             x = {"optimize.agent.recenter-leader.period": None},
             y = {"scopes_avg((delete-create)*avg)": None},
             parameters = {"scenario": None},
             filtering = {"optimize.agent.recenter-leader.enabled": 'true',
                          "optimize.roadsegment.speed-clustering.enabled": 'false',
                          "optimize.agent.recenter-leader.bias": defaultBias
             },
             default = defaults
    )

    graph.xy(recenterLeaderPeriod,
             x = {"optimize.agent.recenter-leader.period": None},
             y = {"roadConn_sum(connect/len(agentConn(id)))": None},
             parameters = {"scenario": None},
             filtering = {"optimize.agent.recenter-leader.enabled": 'true',
                          "optimize.roadsegment.speed-clustering.enabled": 'false',
                          "optimize.agent.recenter-leader.bias": defaultBias
             },
             default = defaults
    )

    graph.xycompare(recenterLeaderPeriod,
                    xy = {"scopes_cdf((delete-create)*avg)": None},
                    parameters = {"optimize.agent.recenter-leader.period": None},
                    filtering = {"optimize.agent.recenter-leader.enabled": 'true',
                                 "optimize.roadsegment.speed-clustering.enabled": 'false',
                                 "scenario": "large-10.xprj",
                                 "optimize.agent.recenter-leader.bias": defaultBias
                    },
                    default = defaults
    )

    graph.xycompare(recenterLeaderPeriod,
                    xy = {"scopes_cdf((delete-create)*avg)": None},
                    parameters = {"scenario": None},
                    filtering = {"optimize.agent.recenter-leader.enabled": 'true',
                                 "optimize.agent.recenter-leader.period": 0,
                                 "optimize.roadsegment.speed-clustering.enabled": 'false',
                                 "optimize.agent.recenter-leader.bias": defaultBias
                    },
                    default = defaults
    )



    graph.backend.closeDocument(recenterLeaderPeriod)

    speedClust = graph.backend.newDocument(path.join(output_dir, "speed_clustering"))
    graph.xy(speedClust,
             x = {"optimize.roadsegment.speed-clustering.factor": None},
             y = {PostFunction("divide", kwparams={"den" : 'roadConn_sum(connect/len(agentConn(id)))', "num" : 'roadInstConn_sum(avg)'}): None},
             parameters = {"scenario": None},
             filtering = {"optimize.roadsegment.speed-clustering.enabled": 'true',
                          "optimize.agent.recenter-leader.enabled": 'false',
                          # "scenario": "/Users/francois/Developpement/Projets/autotopo/sims/scenarios/batch-tests/speed-diff.xprj"
             },
             default = defaults,
             options = {'xlogscale': True}
    )

    #duree de vie des scopes
    graph.xy(speedClust,
             x = {"optimize.roadsegment.speed-clustering.factor": None},
             y = {"scopes_avg((delete-create))": None},
             parameters = {"scenario" : None},
             filtering = {"optimize.roadsegment.speed-clustering.enabled": 'true',
                          "optimize.agent.recenter-leader.enabled": 'false',
                          # "scenario": "/Users/francois/Developpement/Projets/autotopo/sims/scenarios/batch-tests/speed-diff.xprj"
                          },
             default = defaults,
             options = {'xlogscale' : True}
    )

    # graph.xy(speedClust,
    #          x = {"optimize.roadsegment.speed-clustering.factor": None},
    #          y = {"scopes_avg(avg)": None},
    #          parameters = {"scenario": None},
    #          filtering = {"optimize.roadsegment.speed-clustering.enabled": 'true',
    #                       # "scenario": "/Users/francois/Developpement/Projets/autotopo/sims/scenarios/batch-tests/speed-diff.xprj"
    #          }
    # )

    #duree de vie * nombre moyen des scopes
    graph.xycompare(speedClust,
                    xy = {"scopes_cdf((delete-create)*avg)": None},
                    parameters = {"optimize.roadsegment.speed-clustering.factor" : None},
                    filtering = {"optimize.roadsegment.speed-clustering.enabled": 'true',
                                 "scenario": "speed-diff.xprj",
                                 "optimize.agent.recenter-leader.enabled": 'false',
                                 },
                    default = defaults
    )

    graph.backend.closeDocument(speedClust)

    # 'roadsegments.instances.1.end'
    # 'roadsegments.instances.1.next'
    # 'roadsegments.instances.2.end'
    # 'roadsegments.instances.2.next'
    # 'roadsegments.instances.3.next'
    # 'roadsegments.instances.start'
    # 'statistics.roadsegments.2.log'
    # 'scenario'
    # 'duration'
    # 'inflow_mean_q'
    # 'inflow_mean_speed'
    # u'inflow_q_1'
    # u'inflow_q_2'
    # u'inflow_speed_1'
    # u'inflow_speed_2'
    #
    # 'agent.connections.distance.max'
    # 'agent.scope.number.max'
    #
    # 'roadsegments.trafficjam.enabled'
    # 'optimize.agent.recenter-leader.bias'
    # 'optimize.agent.recenter-leader.enabled'
    # 'optimize.agent.recenter-leader.period'
    # 'optimize.anticipation.position.seconds'
    # 'optimize.roadsegment.speed-clustering.enabled'
    # 'optimize.roadsegment.speed-clustering.factor'
    #
    # 'numbers_time,number'
    #
    # 'scopes_avg((delete-create))'
    # 'scopes_avg((delete-create)*avg)'
    # 'scopes_cdf((delete-create))'
    # 'scopes_cdf((delete-create)*avg)'
    # 'scopes_cdf(avg)'
    # 'agentConn_avg(connect/time(time))'
    # 'agentConn_cdf(connect/time(time))'
    # 'agentConn_max(connect/time(time))'
    # 'agentInstConn_avg(avg)'
    # 'agentInstConn_cdf(avg)'
    # 'roadConn_sum(connect/len(agentConn(id)))'
    # 'roadInstConn_sum(avg)'
    # 'timeAgentConn_avg(avg)'
    # 'timeAgentConn_cdf(avg)'
    # 'timeRoadConn_time,avg/numbers(number)'
    #
    # 'acc_avg(cumulatedMinus)'
    # 'acc_avg(cumulatedPlus)'
    # 'acc_cdf(cumulatedMinus)'
    # 'acc_cdf(cumulatedPlus)'
    # 'speed_avg(avg)'
    # 'speed_cdf(avg)'
    # 'speed_std(avg)'
    # 'time_avg(time)'
    # 'time_cdf(time)'

    all_topology(output_dir, graph, defaults)

def all_topology(output_dir, graph, defaults):
    defaultBias = 0
    defaultPeriod = 0
    xy = [
        'agentConn_avg(connect/time(time))',
        'agentInstConn_avg(avg)',
        'roadConn_sum(connect/len(agentConn(id)))',
        'roadInstConn_sum(avg)',
        'scopes_avg((delete-create))',
        'scopes_avg((delete-create)*avg)',
        'timeAgentConn_avg(avg)',
    ]

    xyc = [
        'agentInstConn_cdf(avg)',
        'agentConn_cdf(connect/time(time))',
        'scopes_cdf(avg)',
        'scopes_cdf((delete-create))',
        'scopes_cdf((delete-create)*avg)',
        'timeAgentConn_cdf(avg)',
        # 'timeRoadConn_time,avg/numbers(number)'
    ]

    print graph.storage.get_data().columns.values

    test = graph.backend.newDocument(path.join(output_dir, "test_recenter_period"))

    for y in xy:
        try:
            graph.xy(test,
                     x = {"optimize.agent.recenter-leader.period": None},
                     y = {y: None},
                     parameters = {"scenario": None},
                     filtering = {"optimize.agent.recenter-leader.enabled": 'true',
                                  "optimize.roadsegment.speed-clustering.enabled": 'false',
                                  "optimize.agent.recenter-leader.bias" : defaultBias
                     },
                     default = defaults
            )
        except Exception as e:
            print e
    for y in xyc:
        try:
            graph.xycompare(test,
                            xy = {y: None},
                            parameters = {"optimize.agent.recenter-leader.period": None},
                            filtering = {"optimize.agent.recenter-leader.enabled": 'true',
                                         "optimize.roadsegment.speed-clustering.enabled": 'false',
                                         "scenario": "large-10.xprj",
                                         "optimize.agent.recenter-leader.bias": defaultBias
                            },
                            default = defaults,
                            # options= {'xlogscale' : True}
            )
        except Exception as e:
            print e
    graph.backend.closeDocument(test)

    test = graph.backend.newDocument(path.join(output_dir, "test_recenter_bias"))
    for y in xy:
        try:
            graph.xy(test,
                     x = {"optimize.agent.recenter-leader.bias": None},
                     y = {y: None},
                     parameters = {"scenario": None},
                     filtering = {"optimize.agent.recenter-leader.enabled": 'true',
                                  "optimize.roadsegment.speed-clustering.enabled": 'false',
                                  "optimize.agent.recenter-leader.period": defaultPeriod
                     },
                     default = defaults
            )
        except Exception as e:
            print e
    for y in xyc:
        try:
            graph.xycompare(test,
                            xy = {y: None},
                            parameters = {"optimize.agent.recenter-leader.bias": None},
                            filtering = {"optimize.agent.recenter-leader.enabled": 'true',
                                         "optimize.roadsegment.speed-clustering.enabled": 'false',
                                         "scenario": "large-10.xprj",
                                         "optimize.agent.recenter-leader.period": defaultPeriod
                            },
                            default = defaults,
                            # options = {'xlogscale': True}
            )
        except Exception as e:
            print e
    graph.backend.closeDocument(test)

    test = graph.backend.newDocument(path.join(output_dir, "test_speed_clust"))
    for y in xy:
        try:
            graph.xy(test,
                     x = {"optimize.roadsegment.speed-clustering.factor": None},
                     y = {y: None},
                     parameters = {"scenario": None},
                     filtering = {"optimize.agent.recenter-leader.enabled": 'false',
                                  "optimize.roadsegment.speed-clustering.enabled": 'true',
                     },
                     default = defaults
            )
        except Exception as e:
            print e
    for y in xyc:
        try:
            graph.xycompare(test,
                            xy = {y: None},
                            parameters = {"optimize.roadsegment.speed-clustering.factor": None},
                            filtering = {"optimize.agent.recenter-leader.enabled": 'false',
                                         "optimize.roadsegment.speed-clustering.enabled": 'true',
                                         "scenario": "speed-diff.xprj",
                            },
                            default = defaults
            )
        except Exception as e:
            print e
    graph.backend.closeDocument(test)



if __name__ == "__main__":

    ACTION_WRITE = "write"
    ACTION_GRAPH = "graph"
    import argparse
    import os
    AVAIL_STORAGE = {
        "csv" : PandasCsv,
        "pickle" : PandasPickle,
        "json" : PandasJson,
        "hdf" : PandasHDF,
        "zip" : Zip
    }

    def add_common_arguments(par):
        par.add_argument("--database", default="sims")
        par.add_argument("--storage-type", choices=AVAIL_STORAGE, default="zip")

    parser = argparse.ArgumentParser()

    mode = parser.add_subparsers()
    write = mode.add_parser("write")  # , parents=[parser])
    write.set_defaults(action=ACTION_WRITE)
    write.add_argument("--output-dir", default = "output")
    write.add_argument("--parameters", default = "autotopo-config.properties")

    write.add_argument("--scenario", default = "scenario.xprj")
    add_common_arguments(write)

    # read = mode.add_parser("read")  #, parents=[parser])
    # read.set_defaults(action=ACTION_READ)
    # read.add_argument("--shell", action = 'store_true', default = False)
    # read.add_argument("--database", default="sims.db")

    graph = mode.add_parser("graph")  #, parents=[parser])
    graph.set_defaults(action=ACTION_GRAPH)
    graph.add_argument("--output-dir", default = "graphs")
    add_common_arguments(graph)

    opts = parser.parse_args()
    p = AVAIL_STORAGE[opts.storage_type](opts.database)

    with p as storage:
        if opts.action == ACTION_WRITE:
            print "Recording results into database"
            if isinstance(p, ProcessedStorage):
                storage.prepare()

                params = getParameters(opts.parameters)
                data = readResults(opts.output_dir)
                scenario = getScenario(opts.scenario)
                print "Crunching results"
                res = crunchResults(params, scenario, data)

                storage.write_row(res)
                storage.flush()
            elif isinstance(p, RawStorage):
                storage.prepare()
                print "Storing data"
                config = {
                    "scenario" : opts.scenario,
                    "parameters" : opts.parameters
                }
                storage.store(opts.output_dir, config, os.path.realpath(os.path.join(opts.output_dir, "..")))
                storage.flush()
            print "Results recorded"
        elif opts.action == ACTION_GRAPH:
            if not path.exists(opts.output_dir):
                from os import mkdir

                mkdir(opts.output_dir)
            if isinstance(p, RawStorage):
                print "Extracting results"
                for output_dir, conf in storage.get_results():
                    params = getParameters(conf['parameters'])
                    data = readResults(output_dir)
                    scenario = getScenario(conf['scenario'], output_dir)
                    print "Crunching results"
                    res = crunchResults(params, scenario, data)
                    storage.write_row(res)

            thegraph = Graph(storage)
            makeGraphs(opts.output_dir, thegraph)



## ## ## ## ## ## ## ##
# duree des connections / filtrage connexions courtes ?
# taux de connexion/deconnexion = nombre/duree de parcours ??
# taux de connexion road = nombre de connexion/nombre de voitures ???
# variables "adimentionnees"

# leader bias avec 0.1/0.5
# regarder taux de connection/nombre de connexions instantanees

# ============== #  /!\
# phase 1 => visualisation simplifiee (et comparaison ?)
# phase 2 => test grand nombres + variables interessante

# croiser les scenarios et les techniques

# objectifs => scenario classique ? (qu'est-ce que classique ???)


# motivations : routage + bouchon (si temps)

# ### look at rejection rates for merging.

#trous plus grand entre vagues
