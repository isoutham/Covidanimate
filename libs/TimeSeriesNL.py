import pandas as pd
import geopandas as gpd
import csv

class TimeSeriesNL(object):

    MUNICIPAL = "../CoronaWatchNL/data-geo/data-municipal/RIVM_NL_municipal.csv"
    MAPS = {'Gemeentecode': 'maps/gemeente-2019.geojson',
            'Provincienaam': 'maps/provincies.geojson'
            }
    RECOVERY_WINDOW = 14

    def __init__(self):
        self.target = 'Totaal'
        self.set_gemeente()

    def set_gemeente(self):
        self.key = 'Gemeentecode'
        self.get_maps()

    def set_provincie(self):
        self.key = 'Provincienaam'
        self.get_maps()
        self.map_df.at[2, 'name'] = 'Friesland'

    def is_gemeente(self):
        return self.key == 'Gemeentecode'

    def merge(self):
        if self.is_gemeente():
            self.merged = self.map_df.set_index('Gemnr').join(self.df2)
        else:
            self.merged = self.map_df.set_index('name').join(self.df2)

    def get_maps(self):
        self.map_df = gpd.read_file(self.MAPS[self.key])

    def get_merged(self):
        return self.merged

    def process(self):
        reader = csv.DictReader(open(self.MUNICIPAL))
        data = {}
        dte = ''
        h = None
        for row in reader:
            # ['Datum', 'Gemeentecode', 'Gemeentenaam', 'Provincienaam', 'Provinciecode', 'Type', 'Aantal', 'AantalCumulatief']
            try:
                cnt = int(row['Aantal'])
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
        df = pd.DataFrame.from_dict(data, orient='index')
        df2 = df.copy()
        for col in df.columns:
            df[col + '-rpd'] = df[col].shift(self.RECOVERY_WINDOW)
            df[col + '-cin'] = df[col].cumsum()
            df[col + '-cre'] = df[col + '-rpd'].cumsum()
            df = df.fillna(0)
            df[col + '-cac'] = df[col + '-cin'] - df[col + '-cre']
            df2[col] = df[col + '-cin']
        df2 = df2.T
        if self.is_gemeente():
            df2.index = df2.index.map(int)
        self.df2 = df2

