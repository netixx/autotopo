__author__ = 'francois'

from string import Template
infl = Template('''<Inflow t="$t" q_per_hour="$q" v="$v" />''')

if __name__== '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--waves", type = int, help = "Number of waves of cars", default = 5)
    parser.add_argument("--n", type = int, help = "Number of cars per waves", default = 10)
    parser.add_argument("--duration", type = float, help = "Wave duration (s)", default = 5)
    parser.add_argument("--gap", type = float, help = "Gap between waves (s)", default = 15)
    parser.add_argument("--v", type = float, help = "Speed of cars (m/s)", default = 33)
    parser.add_argument("--lanes", type = int, help = "Number of lanes", default = 10)

    args = parser.parse_args()

    dur = args.duration
    gap = args.gap
    q = args.n/(dur/3600.0)/args.lanes
    t = 0
    for w in xrange(args.waves):
        print infl.substitute(t=t, q=q, v=args.v)
        t = t+dur
        print infl.substitute(t = t, q=q, v =args.v)
        print infl.substitute(t = t, q=0, v = args.v)
        t = t+gap
        print infl.substitute(t = t, q = 0, v=args.v)




