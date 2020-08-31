import sys
from optparse import OptionParser
from libs.TimeSeriesNL import TimeSeriesNL
from libs.Plot import Plot

parser = OptionParser()
parser.add_option("-g", "--gemeente",
                  action="store_true", default=False, dest="gemeente",
                  help="To show Gemeente map (Default)")
parser.add_option("-p", "--provincie",
                  action="store_true", default=False, dest="provincie",
                  help="To show Provincie map")

(options, args) = parser.parse_args()

ts = TimeSeriesNL()
if options.provincie:
    ts.set_provincie()
ts.process()
ts.merge()
plot = Plot(ts)
plot.make_frames()
plot.animate()
sys.exit(0)
