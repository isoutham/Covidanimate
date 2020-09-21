"""Where is Elmer"""
import datetime
import os
import sys
from optparse import OptionParser
import imageio
from libs.combine import Combine
from libs.plot import Plot


def animate():
    """Create movie from frames"""
    images = []
    directory = 'figures5/'
    for filename in os.listdir(directory):
        if filename < '2020-02-28.png':
            continue
        if filename.endswith(".png"):
            images.append(os.path.join(directory, filename))
    idata = []
    for i in sorted(images):
        idata.append(imageio.imread(i))
    filename = 'choropleth.mp4'
    imageio.mimsave(filename, idata)


def parse_regions(region_str):
    """Split a string"""
    if region_str is None:
        return []
    return region_str.split(',')


def process_options():
    """Do what was asked of us"""
    parser = OptionParser()
    parser.add_option("-m", "--map",
                      action="store", default=None, dest="map",
                      help="Call with a date to draw a chorpleth for one date")
    parser.add_option("-g", "--gemeente",
                      action="store_true", default=False, dest="gemeente",
                      help="Draw Gemeente (municipal area) graph, requires -c")
    parser.add_option("-a", "--animation",
                      action="store_true", default=False, dest="animation",
                      help="Make animated chopleth")
    parser.add_option("-r", "--regions",
                      action="store", default=None, dest="regions",
                      help="A comma separated list of regions to graph")
    parser.add_option("-c", "--country",
                      action="store", default=None, dest="country",
                      help="A comma separated list of countries to animate")
    (options, _) = parser.parse_args()
    regions = parse_regions(options.regions)
    combined = Combine()
    combined.parse_countries(options.country)
    combined.process()
    plot = Plot(combined, regions)
    if options.gemeente:
        if len(regions) == 0:
            print('You must specify a region to graph with -g')
            sys.exit(1)
        plot.gemeente_graph()
    if options.animation:
        plot.make_frames()
        animate()
    if options.map is not None:
        date = datetime.datetime.strptime(options.map, '%Y-%m-%d')
        print('Drawing for %s' % date)
        subset = plot.get_one_date(date)
        plot.one_plot(subset, date)

process_options()
sys.exit(0)
