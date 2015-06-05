__author__ = 'francois'

TREATMENT = "treatment"
FILE = "file"
COLS = "columns"


HIST_PARAMS = {
    'min': 0,
    'max': 20,
    'nbins': 12
}

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
        "xy": "{},{}",
        "minus": "({}-{})",
        "mul": "{}*{}"
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
        "minus": np.subtract,
        "mul": np.multiply
    }

    def __getattr__(cls, item):
        return cls.FUNC_MAP[item]


class FuncHelper(object):
    """Properties for making graphs and interface to graph object"""
    __metaclass__ = _FuncHelper

class Function(object):

    def __init__(self, funcs = None, posparams = None, kwparams = None):
        self.posparams = posparams if posparams is None or type(posparams) in (tuple, list) else (posparams,)
        self.kwparams = kwparams

        if type(funcs) in (tuple, list):
            self.funcs = [Function(func, posparams = self.posparams, kwparams= self.kwparams) for func in funcs]
            self.func = None
        else:
            self.func = funcs
            self.funcs = None

    def compute(self, data, defname):
        args = []
        kwargs = {}
        if self.posparams is not None:
            for pparam in self.posparams:
                #param is a function
                if isinstance(pparam, Function):
                    #invoke function recursively
                    args.append(pparam.compute(data, defname))
                else:
                    # print defname
                    #get column
                    args.append(data[defname].getColumn(pparam))
        if self.kwparams is not None:
            for k, v in self.kwparams.iteritems():
                if isinstance(v, Function):
                    kwargs[k] = v.compute(data, defname)
                else:
                    #get column data
                    kwargs[k] = data[defname].getColumn(v)
        if self.funcs is not None:
            return [getattr(FuncHelper, func.func)(*args, **kwargs) for func in self.funcs]
        if self.func is not None:
            return getattr(FuncHelper, self.func)(*args, **kwargs)
        else:
            return args

    def name(self):
        if self.funcs is not None:
            return [repr(func) for func in self.funcs]
        else:
            return repr(self)

    def __repr__(self):
        args = [str(p) for p in self.posparams] if self.posparams is not None else []
        kwargs = {k: str(v) for k, v in self.kwparams.iteritems()} if self.kwparams is not None else {}
        return FuncHelper.getPrintableName(self.func, *args, **kwargs)


class Fetch(Function):
    def __init__(self, name, col):
        Function.__init__(self, "fetch")
        self.name = name
        self.col = col


    def compute(self, data, defname):
        return data[self.name].getColumn(self.col)


    def name(self):
        return repr(self)

    def __repr__(self):
        return "%s(%s)"%(self.name, self.col)
