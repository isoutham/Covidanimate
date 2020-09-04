import sys
from optparse import OptionParser
from libs.TimeSeriesNL import TimeSeriesNL
from libs.TimeSeriesNL import TimeSeriesUK
from libs.Plot import Plot
from libs.Population import PopulationNL
from libs.Population import PopulationUK

parser = OptionParser()
parser.add_option("-n", "--nl",
                  action="store_true", default=False, dest="nl",
                  help="To show NL")
parser.add_option("-u", "--uk",
                  action="store_true", default=False, dest="uk",
                  help="To show UK")

(options, args) = parser.parse_args()

if options.uk:
    ts = TimeSeriesUK()
    ts.process()
    pop = PopulationUK(ts)
if options.nl:
    ts = TimeSeriesNL()
    ts.process()
    pop = PopulationNL(ts)
ts.set_map(pop.get_map())
ts.merge()
plot = Plot(ts)
plot.make_frames()
plot.animate()
sys.exit(0)
