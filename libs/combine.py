"""Store the data in a nice big dataframe"""
import pandas as pd
import geopandas as gpd


class Combine:
    """Combine defined countries together"""

    def __init__(self):
        """Init"""
        self.timeseries = []

    def process(self):
        """Do it"""
        self.timeseries.append(NLTimeseries().get_data())
        self.timeseries.append(UKTimeseries().get_data())
        self.get_combined_data()

    def get(self):
        """Return the data set"""
        return self.merged

    def get_max(self, column):
        """Max value in df"""
        return self.merged[column].max()

    def get_combined_data(self):
        """Get a single dataframe containing all countries we deal with
           I did this so I could draw combined chorpleths but that has Proven
           to be somewhat more challenging than I originally thought
        """
        print('Calculating combined data')
        dataframe = pd.concat(self.timeseries)
        dataframe = dataframe.set_index('Datum')
        dataframe = dataframe.sort_index()
        dataframe['pop_pc'] = dataframe['population'] / 1e5
        # Filter out countries we do not want
        for country in self.countries:
            dataframe = dataframe[~dataframe['country'].isin([country])]
        # Finally create smoothed columns
        dataframe['radaily'] = dataframe.groupby('Gemeentecode',
                                                 sort=False)['Aantal'] \
                                                 .transform(lambda x: x.rolling(7, 1).mean())
        dataframe['radaily_pc'] = dataframe['radaily'] / dataframe['pop_pc']
        print('Finished calculating combined data')
        self.merged = dataframe

    def parse_countries(self, country_str):
        """Sort out country data"""
        all = ['nl', 'sco', 'eng', 'wal', 'ni']
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
        self.countries = list(set(all) - set(ret))
        self.description = '_'.join(ret)


class Timeseries:
    """Abstract class for timeseries"""

    def __init__(self):
        self.merged = None
        self.get_pop()
        self.get_map()
        self.get_source_data()

    def get_data(self):
        """Pass back the data series"""
        return self.merged

    def get_source_data(self):
        """Placeholder"""

    def get_pop(self):
        """Placeholder"""

    def get_map(self):
        """Placeholder"""


class NLTimeseries(Timeseries):
    """Dutch Timeseries"""

    def __init__(self):
        """Init"""
        Timeseries.__init__(self)

    def get_pop(self):
        """Fetch the Population figures for NL"""
        dataframe = pd.read_csv(
            'data/Regionale_kerncijfers_Nederland_31082020_181423.csv', delimiter=';')
        dataframe = dataframe.set_index("Regio")
        dataframe.rename(columns={"aantal": "population"}, inplace=True)
        self.pop = dataframe[dataframe.columns[dataframe.columns.isin(['population'])]]

    def get_source_data(self):
        """Get NL source data for infections"""
        dataframe = pd.read_csv('../CoronaWatchNL/data-geo/data-municipal/RIVM_NL_municipal.csv',
                                delimiter=',')
        dataframe = dataframe[dataframe['Type'] == 'Totaal']
        dataframe['Datum'] = pd.to_datetime(dataframe['Datum'])

        dataframe.drop(columns=['Type', 'Provincienaam', 'Provinciecode'], inplace=True)
        dataframe.dropna(inplace=True)

        dataframe = dataframe.set_index('Gemeentenaam').dropna()
        nlmerged = dataframe.join(self.pop)
        nlmerged.reset_index(inplace=True)
        nlmerged.rename(columns={'index': 'Gemeentenaam'}, inplace=True)
        nlmerged = nlmerged.set_index('Gemeentecode')
        nlmerged = nlmerged.join(self.map)
        nlmerged.reset_index(inplace=True)
        nlmerged = nlmerged.assign(country='nl')
        self.merged = nlmerged

    def get_map(self):
        """Get NL map data"""
        map_df = gpd.read_file('maps/gemeente-2019.geojson')
        #map_df = map_df.reset_index(inplace=True)
        map_df.rename(columns={'Gemeenten_': 'Gemeentecode'}, inplace=True)
        map_df = map_df.set_index("Gemeentecode")
        map_df.drop(columns=['Gemnr', 'Shape_Leng', 'Shape_Area'], inplace=True)
        self.map = map_df


class UKTimeseries(Timeseries):
    """UK Timeseries"""

    def __init__(self):
        """Init"""
        Timeseries.__init__(self)

    def get_pop(self):
        """Fetch the population figures for the UK"""
        dataframe = pd.read_csv('data/ukpop4.csv')
        dataframe = dataframe.set_index("ladcode20")
        dataframe = dataframe.groupby(['ladcode20']).agg(sum)
        dataframe.rename(columns={"population_2019": "population"}, inplace=True)
        self.pop = dataframe[dataframe.columns[dataframe.columns.isin(['population'])]]

    def get_source_data(self):
        """Get UK source data for infections"""
        dataframe = pd.read_csv('data/uk.csv',  delimiter=',')
        dataframe['date'] = pd.to_datetime(dataframe['date'])
        columns = {'date': 'Datum', 'areaName': 'Gemeentenaam',
                   'areaCode': 'Gemeentecode', 'newCasesBySpecimenDate': 'Aantal',
                   'cumCasesBySpecimenDate': 'AantalCumulatief'
                   }
        dataframe.rename(columns=columns, inplace=True)

        dataframe = dataframe.set_index('Gemeentecode').dropna()
        ukmerged = dataframe.join(self.pop)
        ukmerged = ukmerged.join(self.map)
        ukmerged.reset_index(inplace=True)
        ukmerged.rename(columns={'index': 'Gemeentecode'}, inplace=True)
        # <ark the countries for later filtering
        ukmerged.loc[(ukmerged.Gemeentecode.astype(str).str.startswith('S')), 'country'] = 'sco'
        ukmerged.loc[(ukmerged.Gemeentecode.astype(str).str.startswith('W')), 'country'] = 'wal'
        ukmerged.loc[(ukmerged.Gemeentecode.astype(str).str.startswith('E')), 'country'] = 'eng'
        ukmerged.loc[(ukmerged.Gemeentecode.astype(str).str.startswith('N')), 'country'] = 'ni'
        self.merged = ukmerged

    def get_map(self):
        """Get UK Map Data"""
        map_df = gpd.read_file('maps/uk_counties_2020.geojson')
        # Scotland
        # map_df = map_df[~map_df['lad19cd'].astype(str).str.startswith('S')]
        # Northern Ireland
        # map_df = map_df[~map_df['lad19cd'].astype(str).str.startswith('N')]
        map_df.rename(columns={'lad19cd': 'Gemeentecode'}, inplace=True)
        map_df.drop(columns=['lad19nm', 'lad19nmw', 'st_areashape',
                             'st_lengthshape', 'bng_e', 'bng_n', 'long', 'lat'], inplace=True)
        map_df = map_df.set_index("Gemeentecode")
        self.map = map_df
