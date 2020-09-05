"""Import timeseries data"""
import csv
import math
import pandas as pd
import geopandas as gpd
import numpy as np


class TimeSeries:
    """Dumb abstract class for country timeseries"""

    RECOVERY_WINDOW = 14
    cc = 'No country'
    MAPS = {}
    key = ''

    def __init__(self):
        self.map_df = None
        self.gemsdf = None
        self.target = 'Totaal'
        self.merged = pd.DataFrame()
        self.df2 = None
        self.get_maps()

    def get_maps(self):
        """Return a geopandas map object"""
        if self.map_df is None:
            self.map_df = gpd.read_file(self.MAPS[self.key])
        return self.map_df

    def get_max(self):
        """Return the maximum value in the timeseries"""
        maxc = ''
        for column in self.merged.columns:
            if column.startswith('20'):
                if column > maxc:
                    maxc = column
        maxval = self.merged[maxc].max()
        return int(math.ceil(maxval / 100.0)) * 100

    def set_map(self, dataframe):
        """Replace the map object with a merged dataframe containing population data"""
        self.map_df = dataframe

    def get_merged(self):
        """Return the merged dataframe"""
        return self.merged

    def get_cc(self):
        """Get the country code"""
        return self.cc


class TimeSeriesUK(TimeSeries):
    """England"""

    MUNICIPAL = "data/uk.csv"
    MAPS = {'Counties': 'maps/uk_counties.geojson'
            }
    key = 'Counties'
    cc = 'England'

    def process(self):
        """Process the raw data and create a dataframe"""
        reader = csv.DictReader(open(self.MUNICIPAL))
        data = {}
        dte = ''
        for row in reader:
            # date', 'areaName', 'areaCode', 'cumCasesBySpecimenDate'
            try:
                cnt = float(row['cumCasesBySpecimenDate'])
            except ValueError:
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
        self.df2 = pd.DataFrame.from_dict(data, orient='columns')

    def merge(self):
        """Create a dataframe with map population and counts"""
        self.merged = self.map_df.join(self.df2)
        self.merged.replace(r'\s+', np.nan, regex=True, inplace=True)
        self.merged.fillna(0, inplace=True)
        self.do_calculations()

    def do_calculations(self):
        """Make calculations"""
        self.merged['population'] = self.merged['population'].str.replace('.', '')
        self.merged['population'] = self.merged['population'].astype(float)
        for column in self.merged.columns:
            if column.startswith('20'):
                self.merged[column] = self.merged[column] / \
                    (self.merged['population'] / 100000)


class TimeSeriesNL(TimeSeries):
    """The Netherlands"""

    MUNICIPAL = "../CoronaWatchNL/data-geo/data-municipal/RIVM_NL_municipal.csv"
    MAPS = {'Gemeentecode': 'maps/gemeente-2019.geojson',
            'Provincienaam': 'maps/provincies.geojson'
            }
    key = 'Gemeentecode'

    cc = 'The Netherlands'

    def merge(self):
        """"Merge dataframe with map population and counts"""
        self.merged = self.map_df.join(self.df2)
        self.do_calculations()

    def do_calculations(self):
        """Make calculations"""
        for column in self.merged.columns:
            if column.startswith('20'):
                self.merged[column] = self.merged[column] / \
                    (self.merged['aantal'] / 100000)

    def process(self):
        """Get raw data into a suitable timeseries dataframe"""
        reader = csv.DictReader(open(self.MUNICIPAL))
        data = {}
        gems = {}
        dte = ''
        for row in reader:
            gems[row['Gemeentenaam']] = row['Gemeentecode']
            try:
                cnt = int(row['AantalCumulatief'])
            except ValueError:
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
        dataframe = pd.DataFrame.from_dict(data, orient='columns')
        self.gemsdf = pd.DataFrame(list(gems.items()),
                                   columns=['name', 'code'])
        dataframe.index = dataframe.index.map(int)
        self.df2 = dataframe
