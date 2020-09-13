"""Where is Elmer"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import datetime
import os
import imageio


def get_pop():
    df = pd.read_csv('data/ukpop4.csv')
    df = df.set_index("ladcode20")
    df = df.groupby(['ladcode20']).agg(sum)
    df.rename(columns={"population_2019": "population"}, inplace=True)
    return df

def get_source_data():
    dataframe = pd.read_csv('data/uk.csv',  delimiter=',')
    dataframe['date'] = pd.to_datetime(dataframe['date'])
    return dataframe

def get_data(src, dat):
    start = dat - datetime.timedelta(days=10)
    # Filter the frame
    dataframe = src[src['date'] >= start]
    dataframe = dataframe[dataframe['date'] <= dat]
    # Group England, Wales, Scotland and NI by date
    dataframe = dataframe.groupby(['areaCode']).agg(sum)
    return dataframe

def get_map():
    map_df = gpd.read_file('maps/uk_counties_2020.geojson')
    # Scotland
    map_df = map_df[~map_df['lad19cd'].astype(str).str.startswith('S')]
    # Northern Ireland
    map_df = map_df[~map_df['lad19cd'].astype(str).str.startswith('N')]
    map_df = map_df.set_index("lad19cd")
    return map_df

def get_one_date(dat, src, map, pop):
    col ='newCasesBySpecimenDate'
    data = get_data(src, dat)
    merged = map.join(data,  how='outer')
    merged = merged.join(pop,  how='outer')
    merged['pc'] = merged[col] / (merged['population']/ 1e5)
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
    plt.savefig('figures4/%s.png' % date.strftime('%Y-%m-%d'))
    plt.close(fig)

def animate():
    images = []
    directory = 'figures4/'
    for filename in os.listdir(directory):
        print(filename)
        if filename < '2020-03-15.png':
            continue
        if filename.endswith(".png"):
            images.append(os.path.join(directory, filename))
    idata = []
    for i in sorted(images):
        idata.append(imageio.imread(i))
    filename = '%s_choropleth.mp4' % 'UK Hotspots'
    imageio.mimsave(filename, idata)

def make_frames():
    pop = get_pop()
    map = get_map()
    src = get_source_data()

    for dat in list(set(src['date'])):
        print(dat)
        merged = get_one_date(dat, src, map, pop)
        one_plot(merged, dat)

make_frames()
animate()
