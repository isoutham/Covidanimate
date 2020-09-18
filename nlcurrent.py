"""Where is Elmer"""
import datetime
import os
import sys
import imageio
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from optparse import OptionParser


def get_nl_pop():
    """Fetch the Population figures for NL"""
    dataframe = pd.read_csv('data/Regionale_kerncijfers_Nederland_31082020_181423.csv', delimiter=';')
    dataframe = dataframe.set_index("Regio")
    dataframe.rename(columns={"aantal": "population"}, inplace=True)
    return dataframe[dataframe.columns[dataframe.columns.isin(['population'])]]

def get_uk_pop():
    """Fetch the population figures for the UK"""
    dataframe = pd.read_csv('data/ukpop4.csv')
    dataframe = dataframe.set_index("ladcode20")
    dataframe = dataframe.groupby(['ladcode20']).agg(sum)
    dataframe.rename(columns={"population_2019": "population"}, inplace=True)
    return dataframe[dataframe.columns[dataframe.columns.isin(['population'])]]

def get_combined_data():
    """Get a single dataframe containing all countries we deal with"""
    nlpop = get_nl_pop()
    ukpop = get_uk_pop()
    nldata = get_nl_source_data()
    ukdata = get_uk_source_data()
    columns = {'date': 'Datum', 'areaName': 'Gemeentenaam',
               'areaCode': 'Gemeentecode', 'newCasesBySpecimenDate': 'Aantal',
               'cumCasesBySpecimenDate': 'AantalCumulatief'
               }
    ukdata.rename(columns=columns, inplace=True)
    nldata.drop(columns=['Type', 'Provincienaam', 'Provinciecode'], inplace=True)
    nldata.dropna(inplace=True)

    nldata = nldata.set_index('Gemeentenaam').dropna()
    nlmerged = nldata.join(nlpop)

    ukdata = ukdata.set_index('Gemeentecode').dropna()
    ukmerged = ukdata.join(ukpop)

    ukmerged.reset_index(inplace=True)
    nlmerged.reset_index(inplace=True)
    ukmerged.rename(columns= {'index': 'Gemeentecode'}, inplace=True)
    nlmerged.rename(columns= {'index': 'Gemeentenaam'}, inplace=True)
    dataframe = pd.concat([ukmerged, nlmerged])
    dataframe = dataframe.set_index('Datum')
    return dataframe

def get_nl_source_data():
    """Get NL source data for infections"""
    dataframe = pd.read_csv('../CoronaWatchNL/data-geo/data-municipal/RIVM_NL_municipal.csv',
                             delimiter=',')
    dataframe = dataframe[dataframe['Type'] == 'Totaal']
    dataframe['Datum'] = pd.to_datetime(dataframe['Datum'])
    return dataframe

def get_uk_source_data():
    """Get UK source data for infections"""
    dataframe = pd.read_csv('data/uk.csv',  delimiter=',')
    dataframe['date'] = pd.to_datetime(dataframe['date'])
    return dataframe

def pcols(frame):
    """Print columns (sometimes handy)"""
    for column in frame.columns:
        print(column)

def get_data(src, dat):
    """Get data for one day"""
    dataframe = src
    if dat is not None:
        start = dat - datetime.timedelta(days=10)
        # Filter the frame
        dataframe = src[src['Datum'] >= start]
        dataframe = dataframe[dataframe['Datum'] <= dat]
        #dataframe = dataframe.groupby(['    aaa
    dataframe = dataframe.set_index('Gemeentecode')
    return dataframe

def get_nl_map():
    """Get NL map data"""
    map_df = gpd.read_file('maps/gemeente-2019.geojson')
    map_df = map_df.set_index("Gemeenten_")
    return map_df

def get_one_date(dat, src, map, pop):
    """Data for one data (for animation)"""
    col ='Aantal'
    data = get_data(src, dat)
    merged = map.join(data,  how='outer')
    merged = merged.set_index('Gemeentenaam').dropna()
    merged = merged.join(pop,  how='outer')
    merged = merged.dropna()
    merged = merged.groupby(merged.index).agg({'Gemnr': 'first', 'Aantal': 'sum', 'Datum': 'first',
                                               'population':  'first', 'geometry': 'first'})
    merged['pc'] = merged[col] / (merged['population']/ 1e5)
    if dat is not None:
        merged = gpd.GeoDataFrame(merged)
    return merged

def one_plot(merged, date):
    """Create one Chorpleth"""
    cmap = 'Oranges'
    plt.style.use('dark_background')
    fig, axis = plt.subplots(1, figsize=(7, 8.5))
    style_kwds = {
        'linewidth': 1,
        'markersize': 2,
        'facecolor': 'black',
        'edgecolor': 'black'
    }
    print(merged['pc'].max())
    axis.set_title(date.strftime('%d-%m-%Y'), color='white', fontsize=20)
    merged.plot(column='pc', vmax=200, vmin=0,
                ax=axis, legend=False,
                cmap=cmap, **style_kwds)
    axis.axis('off')
    #plt.figtext(0.3, 0.14, "Covid Confirmed Cases per 100.000 inhabitants",
                #ha="center",
                #fontsize=12, bbox={"facecolor": "white", "alpha": 0.5, "pad": 5})
    plt.tight_layout(pad=0.1)
    plt.savefig('figures5/%s.png' % date.strftime('%Y-%m-%d'))
    plt.close(fig)

def animate():
    """Create movie from frames"""
    images = []
    directory = 'figures5/'
    for filename in os.listdir(directory):
        if filename < '2020-02-28.png':
            continue
        print(filename)
        if filename.endswith(".png"):
            images.append(os.path.join(directory, filename))
    idata = []
    for i in sorted(images):
        idata.append(imageio.imread(i))
    filename = '%s_choropleth.mp4' % 'NL_Hotspots'
    imageio.mimsave(filename, idata)

def make_frames():
    """Create a frame for all available dates"""
    pop = get_nl_pop()
    map = get_nl_map()
    src = get_nl_source_data()

    for dat in list(set(src['Datum'])):
        merged = get_one_date(dat, src, map, pop)
        one_plot(merged, dat)

def gemeente_graph(gemeenten):
    """Graphs by local municipality (gemeente)"""
    merged = get_combined_data()
    merged['pc'] = merged['AantalCumulatief'] / (merged['population']/ 1e5)
    merged['pcr'] = merged['pc'].rolling(window=7).mean()
    plt.style.use('dark_background')
    _, axis = plt.subplots(1, figsize=(10, 7))
    plt.xlabel("Date")
    plt.ylabel("Infections per 100.100 Rolling 7 day average")
    axis.set_title('Covid-19', color='white', fontsize=20)
    gems = {}
    for gemeente in gemeenten:
        gems[gemeente] = merged[merged['Gemeentenaam'] == gemeente]
        print(gems[gemeente])
        gems[gemeente].plot(y='pcr', label=gemeente, ax=axis)
    plt.grid(which='major', alpha=0.5)
    plt.grid(which='minor', alpha=0.2)
    plt.tight_layout(pad=2)
    plt.savefig('Gemeenten.png')

def parse_regions(region_str):
    if region_str is None:
        return []
    return region_str.split(',')

def parse_countries(country_str):
    if country_str is None:
        return ['NL']
    return country_str.split(',')

def process_options():
    """Do what was asked of us"""
    parser = OptionParser()
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
    countries = parse_countries(options.country)
    if options.gemeente:
        if len(regions) == 0:
            print('You must specify a region to graph with -g')
            sys.exit(1)
        gemeente_graph(regions)
    if options.animation:
        # TODO Implement countries
        make_frames()
        animate()

process_options()
sys.exit(0)
