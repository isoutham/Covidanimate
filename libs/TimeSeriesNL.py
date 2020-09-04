import pandas as pd
import geopandas as gpd
import csv
import math
import matplotlib.pyplot as plt
import numpy as np


class TimeSeries(object):

    RECOVERY_WINDOW = 14

    def __init__(self):
        self.map_df = None
        self.gemsdf = None
        self.target = 'Totaal'
        self.get_maps()

    def get_maps(self):
        if self.map_df is None:
            self.map_df = gpd.read_file(self.MAPS[self.key])
        return self.map_df

    def get_max(self):
        maxc = ''
        for column in self.merged.columns:
            if column.startswith('20'):
                if column > maxc:
                    maxc = column
        maxval = self.merged[maxc].max()
        return int(math.ceil(maxval / 100.0)) * 100

    def set_map(self, df):
        self.map_df = df

    def get_merged(self):
        return self.merged

    def get_cc(self):
        return self.cc

class TimeSeriesUK(TimeSeries):

    MUNICIPAL = "data/uk.csv"
    MAPS = {'Counties': 'maps/uk_counties.geojson'
            }
    key = 'Counties'
    cc = 'England'

    def __init__(self):
        super(TimeSeriesUK, self).__init__()

    def process(self):
        reader = csv.DictReader(open(self.MUNICIPAL))
        data = {}
        dte = ''
        h = None
        for row in reader:
            # date', 'areaName', 'areaCode', 'cumCasesBySpecimenDate'
            try:
                cnt = float(row['cumCasesBySpecimenDate'])
            except:
                cnt = 0
            if not row['areaCode'].startswith('E'):
                continue
            dte = row['date']
            if row['date'] not in data:
                data[row['date']] = {}
            if row['areaCode'] not in data[row['date']]:
                data[row['date']][row['areaCode']] = 0

                if cnt > 0:
                    data[dte][row['areaCode']] += cnt
        df = pd.DataFrame.from_dict(data, orient='columns')
        self.df2 = df

    def merge(self):
        self.merged = self.map_df.join(self.df2)
        self.merged.replace(r'\s+', np.nan, regex=True, inplace=True)
        self.merged.fillna(0, inplace=True)
        self.do_calculations()

    def do_calculations(self):
        self.merged['population'] = self.merged['population'].str.replace('.','')
        self.merged['population'] = self.merged['population'].astype(float)
        for column in self.merged.columns:
            if column.startswith('20'):
                self.merged[column] = self.merged[column] / \
                    (self.merged['population'] / 100000)


class TimeSeriesNL(TimeSeries):

    MUNICIPAL = "../CoronaWatchNL/data-geo/data-municipal/RIVM_NL_municipal.csv"
    MAPS = {'Gemeentecode': 'maps/gemeente-2019.geojson',
            'Provincienaam': 'maps/provincies.geojson'
            }
    key = 'Gemeentecode'

    cc = 'The Netherlands'

    def __init__(self):
        super(TimeSeriesNL, self).__init__()

    def merge(self):
        self.merged = self.map_df.join(self.df2)
        self.do_calculations()

    def do_calculations(self):
        for column in self.merged.columns:
            if column.startswith('20'):
                self.merged[column] = self.merged[column] / \
                    (self.merged['aantal'] / 100000)

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
