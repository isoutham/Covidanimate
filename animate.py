import sys
from optparse import OptionParser
from libs.TimeSeriesNL import TimeSeriesNL
from libs.Plot import Plot
from libs.Population import Population

parser = OptionParser()
parser.add_option("-g", "--gemeente",
                  action="store_true", default=False, dest="gemeente",
                  help="To show Gemeente map (Default)")

(options, args) = parser.parse_args()

ts = TimeSeriesNL()
ts.process()
pop = Population(ts)
ts.set_map(pop.get_map())
ts.merge()
plot = Plot(ts)
plot.make_frames()
plot.animate()
sys.exit(0)