"""Where is Elmer"""
import datetime
import os
import glob
import sys
from optparse import OptionParser
import imageio
from libs.combine import Combine
from libs.plot import Plot


DIRECTORY = 'figures5/'

def animate():
    """Create movie from frames"""
    images = []
    for filename in os.listdir(DIRECTORY):
        if filename < '2020-03-23.png':
            continue
        if filename.endswith(".png"):
            images.append(os.path.join(DIRECTORY, filename))
    idata = []
    for i in sorted(images):
        idata.append(imageio.imread(i))
    filename = 'choropleth.mp4'
    imageio.mimsave(filename, idata, fps=3)

def clear_images():
    """Clean up previous runs"""
    files = glob.glob(f'{DIRECTORY}/*.png')
    for file in files:
        os.remove(file)

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
    parser.add_option("-l", "--league",
                      action="store_true", default=False, dest="league",
                      help="League table by Gemeente")
    parser.add_option("-n", "--nation",
                      action="store_true", default=False, dest="nation",
                      help="Data by Nation")
    parser.add_option("-s", "--start",
                      action="store", default=None, dest="startdate",
                      help="Start date from animation yyyymmdd")
    parser.add_option("-e", "--end",
                      action="store", default=None, dest="enddate",
                      help="Start date from animation yyyymmdd")
    parser.add_option("-z", "--hospital",
                      action="store_true", default=False, dest="hospital",
                      help="Show hospital admissions if data is available")
    parser.add_option("-p", "--pivot",
                      action="store_true", default=False, dest="pivot",
                      help="Pivot Data Set")

    (options, _) = parser.parse_args()
    regions = parse_regions(options.regions)
    combined = Combine(options)
    combined.parse_countries(options.country)

    combined.process()
    plot = Plot(combined, regions)
    if options.pivot:
        plot.pivot_graph()
        return
    if options.gemeente:
        if len(regions) == 0:
            print('You must specify a region to graph with -g')
            sys.exit(1)
        plot.gemeente_graph()
    if options.league:
        combined.project_for_date(None)
    if options.nation:
        if options.animation:
            plot.nations_animate()
            return
        plot.nations()
    if options.animation:
        clear_images()
        plot.make_frames()
        animate()
    if options.map is not None:
        date = datetime.datetime.strptime(options.map, '%Y-%m-%d')
        print('Drawing for %s' % date)
        subset = plot.get_one_date(date)
        print(subset)
        plot.one_plot(subset, date)

process_options()
sys.exit(0)
