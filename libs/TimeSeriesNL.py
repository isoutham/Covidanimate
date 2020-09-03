import pandas as pd
import geopandas as gpd
import csv
import math


class TimeSeriesNL(object):

    MUNICIPAL = "../CoronaWatchNL/data-geo/data-municipal/RIVM_NL_municipal.csv"
    MAPS = {'Gemeentecode': 'maps/gemeente-2019.geojson',
            'Provincienaam': 'maps/provincies.geojson'
            }
    key = 'Gemeentecode'
    RECOVERY_WINDOW = 14

    def __init__(self):
        self.map_df = None
        self.gemsdf = None
        self.target = 'Totaal'
        self.get_maps()

    def merge(self):
        self.merged = self.map_df.join(self.df2)
        self.do_calculations()

    def do_calculations(self):
        for column in self.merged.columns:
            if column.startswith('20'):
                self.merged[column] = self.merged[column] / \
                    (self.merged['aantal'] / 100000)

    def get_max(self):
        maxval = self.merged[self.merged.columns[-1]].max()
        return int(math.ceil(maxval / 100.0)) * 100

    def get_maps(self):
        if self.map_df is None:
            self.map_df = gpd.read_file(self.MAPS[self.key])
        return self.map_df

    def set_map(self, df):
        self.map_df = df

    def get_merged(self):
        return self.merged

    def process(self):
        reader = csv.DictReader(open(self.MUNICIPAL))
        data = {}
        gems = {}
        dte = ''
        h = None
        for row in reader:
            # ['Datum', 'Gemeentecode', 'Gemeentenaam', 'Provincienaam', 'Provinciecode', 'Type', 'Aantal', 'AantalCumulatief']
            gems[row['Gemeentenaam']] = row['Gemeentecode']
            try:
                cnt = int(row['AantalCumulatief'])
            except:
                cnt = 0
            if row[self.key] == '':
                continue
            dte = row['Datum']
            if row['Datum'] not in data:
                data[row['Datum']] = {}
            if row[self.key] not in data[row['Datum']]:
                data[row['Datum']][row[self.key]] = 0

            if self.target == row['Type']:
                if cnt > 0:
                    data[dte][row[self.key]] += cnt
        df = pd.DataFrame.from_dict(data, orient='columns')
        self.gemsdf = pd.DataFrame(list(gems.items()),
                                   columns=['name', 'code'])
        df.index = df.index.map(int)
        self.df2 = df
