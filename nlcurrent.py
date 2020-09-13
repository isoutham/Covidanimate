"""Where is Elmer"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import datetime
import os
import imageio


def get_pop():
    df = pd.read_csv('data/Regionale_kerncijfers_Nederland_31082020_181423.csv', delimiter=';')
    df = df.set_index("Regio")
    df.rename(columns={"aantal": "population"}, inplace=True)
    return df

def get_source_data():
    dataframe = pd.read_csv('../CoronaWatchNL/data-geo/data-municipal/RIVM_NL_municipal.csv',  delimiter=',')
    dataframe = dataframe[dataframe['Type'] == 'Totaal']
    dataframe['Datum'] = pd.to_datetime(dataframe['Datum'])
    return dataframe

def pcols(frame):
    for column in frame.columns:
        print(column)

def get_data(src, dat):
    start = dat - datetime.timedelta(days=10)
    # Filter the frame
    dataframe = src[src['Datum'] >= start]
    dataframe = dataframe[dataframe['Datum'] <= dat]
    #dataframe = dataframe.groupby(['    aaa
    dataframe = dataframe.set_index('Gemeentecode')
    return dataframe

def get_map():
    map_df = gpd.read_file('maps/gemeente-2019.geojson')
    map_df = map_df.set_index("Gemeenten_")
    return map_df

def get_one_date(dat, src, map, pop):
    col ='Aantal'
    data = get_data(src, dat)
    merged = map.join(data,  how='outer')
    merged = merged.set_index('Gemeentenaam').dropna()
    merged = merged.join(pop,  how='outer')
    merged = merged.dropna()
    merged = merged.groupby(merged.index).agg({'Aantal': 'sum', 'population':  'first', 'geometry': 'first'})
    merged['pc'] = merged[col] / (merged['population']/ 1e5)
    merged = gpd.GeoDataFrame(merged)
    return merged

def one_plot(merged, date):
    cmap = 'Oranges'
    plt.style.use('dark_background')
    fig, axis = plt.subplots(1, figsize=(7, 10))
    style_kwds = {
        'linewidth': 1,
        'markersize': 2,
        'facecolor': 'black',
        'edgecolor': 'black'
    }
    axis.set_title(date.strftime('%d-%m-%Y'), color='white', fontsize=20)
    merged.plot(column='pc', vmax=100, vmin=0,
                ax=axis, legend=False,
                cmap=cmap, **style_kwds)
    axis.axis('off')
    plt.figtext(0.5, 0.05, "Covid Confirmed Cases per 100.000 inhabitants",
                ha="center",
                fontsize=12, bbox={"facecolor": "white", "alpha": 0.5, "pad": 5})
    plt.savefig('figures5/%s.png' % date.strftime('%Y-%m-%d'))
    plt.close(fig)

def animate():
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
    pop = get_pop()
    map = get_map()
    src = get_source_data()

    count = 0
    for dat in list(set(src['Datum'])):
        merged = get_one_date(dat, src, map, pop)
        one_plot(merged, dat)
        count += 1
        #if count > 5:
           #break

make_frames()
animate()
