"""Where is Elmer"""
import datetime
import os
import sys
from optparse import OptionParser
import imageio
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt


def get_nl_pop():
    """Fetch the Population figures for NL"""
    dataframe = pd.read_csv(
        'data/Regionale_kerncijfers_Nederland_31082020_181423.csv', delimiter=';')
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


def get_uk_source_data():
    """Get UK source data for infections"""
    ukpop = get_uk_pop()
    dataframe = pd.read_csv('data/uk.csv',  delimiter=',')
    dataframe['date'] = pd.to_datetime(dataframe['date'])
    columns = {'date': 'Datum', 'areaName': 'Gemeentenaam',
               'areaCode': 'Gemeentecode', 'newCasesBySpecimenDate': 'Aantal',
               'cumCasesBySpecimenDate': 'AantalCumulatief'
               }
    dataframe.rename(columns=columns, inplace=True)

    dataframe = dataframe.set_index('Gemeentecode').dropna()
    ukmerged = dataframe.join(ukpop)
    map_df = get_uk_map()
    ukmerged = ukmerged.join(map_df)
    ukmerged.reset_index(inplace=True)
    ukmerged.rename(columns={'index': 'Gemeentecode'}, inplace=True)
    # <ark the countries for later filtering
    ukmerged.loc[(ukmerged.Gemeentecode.astype(str).str.startswith('S')),'country']='sco'
    ukmerged.loc[(ukmerged.Gemeentecode.astype(str).str.startswith('W')),'country']='wal'
    ukmerged.loc[(ukmerged.Gemeentecode.astype(str).str.startswith('E')),'country']='eng'
    ukmerged.loc[(ukmerged.Gemeentecode.astype(str).str.startswith('N')),'country']='ni'
    return ukmerged


def get_nl_source_data():
    """Get NL source data for infections"""
    nlpop = get_nl_pop()
    dataframe = pd.read_csv('../CoronaWatchNL/data-geo/data-municipal/RIVM_NL_municipal.csv',
                            delimiter=',')
    dataframe = dataframe[dataframe['Type'] == 'Totaal']
    dataframe['Datum'] = pd.to_datetime(dataframe['Datum'])

    dataframe.drop(columns=['Type', 'Provincienaam', 'Provinciecode'], inplace=True)
    dataframe.dropna(inplace=True)

    dataframe = dataframe.set_index('Gemeentenaam').dropna()
    nlmerged = dataframe.join(nlpop)
    nlmerged.reset_index(inplace=True)
    nlmerged.rename(columns={'index': 'Gemeentenaam'}, inplace=True)
    nlmerged = nlmerged.set_index('Gemeentecode')
    map_df = get_nl_map()
    nlmerged = nlmerged.join(map_df)
    nlmerged.reset_index(inplace=True)
    nlmerged = nlmerged.assign(country='nl')
    return nlmerged


def get_combined_data(countries):
    """Get a single dataframe containing all countries we deal with
       I did this so I could draw combined chorpleths but that has Proven
       to be somewhat more challenging than I originally thought
    """
    print('Calculating combined data')
    nldata = get_nl_source_data()
    ukdata = get_uk_source_data()
    dataframe = pd.concat([ukdata, nldata])
    dataframe = dataframe.set_index('Datum')
    dataframe = dataframe.sort_index()
    dataframe['pop_pc'] = dataframe['population'] / 1e5
    # Filter out countries we do not want
    for country in countries:
        dataframe = dataframe[~dataframe['country'].isin([country])]
    # Finally create smoothed columns
    dataframe['radaily'] = dataframe.groupby('Gemeentecode', sort=False)['Aantal'].transform(lambda x: x.rolling(7, 1).mean())
    dataframe['radaily_pc'] = dataframe['radaily'] / dataframe['pop_pc']
    print('Finished calculating combined data')
    return dataframe

def get_max(dataframe, column):
    return dataframe[column].max()

def pcols(frame):
    """Print columns (sometimes handy)"""
    for column in frame.columns:
        print(column)

def get_nl_map():
    """Get NL map data"""
    map_df = gpd.read_file('maps/gemeente-2019.geojson')
    #map_df = map_df.reset_index(inplace=True)
    map_df.rename(columns={'Gemeenten_': 'Gemeentecode'}, inplace=True)
    map_df = map_df.set_index("Gemeentecode")
    map_df.drop(columns=['Gemnr', 'Shape_Leng', 'Shape_Area'], inplace=True)
    return map_df

def get_uk_map():
    """Get UK Map Data"""
    map_df = gpd.read_file('maps/uk_counties_2020.geojson')
    # Scotland
    # map_df = map_df[~map_df['lad19cd'].astype(str).str.startswith('S')]
    # Northern Ireland
    # map_df = map_df[~map_df['lad19cd'].astype(str).str.startswith('N')]
    map_df.rename(columns={'lad19cd': 'Gemeentecode'}, inplace=True)
    map_df.drop(columns=['lad19nm', 'lad19nmw', 'st_areashape',
                         'st_lengthshape', 'bng_e','bng_n','long', 'lat'], inplace=True)
    map_df = map_df.set_index("Gemeentecode")
    return map_df

def get_one_date(dat, src):
    """Data for one date (for animation)"""
    col = 'Aantal'
    data = src[src.index == dat]
    return gpd.GeoDataFrame(data)


def one_plot(merged, date):
    """Create one Chorpleth"""
    print("Creating a single frame")
    cmap = 'Oranges'
    plt.style.use('dark_background')
    fig, axis = plt.subplots(1, figsize=(7, 8.5))
    style_kwds = {
        'linewidth': 1,
        'markersize': 2,
        'facecolor': 'black',
        'edgecolor': 'black'
    }
    axis.set_title(date.strftime('%d-%m-%Y'), color='white', fontsize=20)
    merged.plot(column='radaily_pc', vmax=get_max(merged, 'radaily_pc'), vmin=0,
                ax=axis, legend=False,
                cmap=cmap, **style_kwds)
    axis.axis('off')
    # plt.figtext(0.3, 0.14, "Covid Confirmed Cases per 100.000 inhabitants",
    # ha="center",
    # fontsize=12, bbox={"facecolor": "white", "alpha": 0.5, "pad": 5})
    plt.tight_layout(pad=0.1)
    plt.savefig('figures5/%s.png' % date.strftime('%Y-%m-%d'))
    plt.close(fig)
    print("Finished reating a single frame")


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
    filename = '%s_choropleth.mp4' % 'NL_Hotspots'
    imageio.mimsave(filename, idata)


def make_frames(src):
    """Create a frame for all available dates"""
    for dat in list(set(src.index)):
        print(dat)
        merged = get_one_date(dat, src)
        one_plot(merged, dat)


def gemeente_graph(gemeenten, merged):
    """Graphs by local municipality (gemeente)"""
    plt.style.use('dark_background')
    _, axis = plt.subplots(1, figsize=(14, 7))
    plt.xlabel("Date")
    plt.ylabel("Daily Cases per 100.000 - rolling 7 day mean")
    axis.set_title('Covid-19', color='white', fontsize=20)
    for gemeente in gemeenten:
        gem = merged[merged['Gemeentenaam'] == gemeente]
        #gem = gem.replace({'AantalCumulatief': {0: np.nan}}).ffill()
        #gem['infected'] = gem.Aantal.rolling(window=3, min_periods=0).sum()
        gem.plot(y='radaily_pc', label=gemeente, ax=axis)
    plt.grid(which='major', alpha=0.5)
    plt.grid(which='minor', alpha=0.2)
    plt.tight_layout(pad=2)
    plt.savefig('Gemeenten.png')


def parse_regions(region_str):
    if region_str is None:
        return []
    return region_str.split(',')


def parse_countries(country_str):
    all = [ 'nl', 'sco', 'eng', 'wal', 'ni']
    ret = []
    if country_str is None:
        country_list = all
    else:
        country_list = country_str.split(',')
    for country in country_list:
        country = country.lower()
        if 'nether' in country:
            country = 'nl'
        if 'scot' in country:
            country = 'sco'
        if 'eng' in country:
            country = 'eng'
        if 'wal' in country:
            country = 'wal'
        if 'ire' in country:
            country = 'ni'
        ret.append(country)
    return list(set(all) - set(ret))



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
    countries = parse_countries(options.country)
    src = get_combined_data(countries)
    if options.gemeente:
        if len(regions) == 0:
            print('You must specify a region to graph with -g')
            sys.exit(1)
        gemeente_graph(regions, src)
    if options.animation:
        make_frames(src)
        animate()
    if options.map is not None:
        date = datetime.datetime.strptime(options.map, '%Y-%m-%d')
        print('Drawing for %s' % date)
        merged = get_one_date(date, src)
        one_plot(merged, date)

process_options()
sys.exit(0)
