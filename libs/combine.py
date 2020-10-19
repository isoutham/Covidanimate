"""Store the data in a nice big dataframe"""
from datetime import datetime, timedelta
import datetime
import pandas as pd
import geopandas as gpd


class Combine:
    """Combine defined countries together"""

    def __init__(self, options):
        """Init"""
        self.options = options
        self.timeseries = []
        self.countries = None
        self.description = None
        self.merged = None
        self.cc = None
        self.populations = []
        self.national_populations = None

    def process(self):
        """Do it"""
        if self.options.nation:
            self.timeseries.append(BETimeseries(False).national())
            self.timeseries.append(UKTimeseries(False).national())
            self.timeseries.append(NLTimeseries(False).national())
            self.combine_national()
        else:
            self.timeseries.append(DETimeseries().get_data())
            self.timeseries.append(BETimeseries().get_data())
            self.timeseries.append(NLTimeseries().get_data())
            self.timeseries.append(UKTimeseries().get_data())
            self.get_combined_data()

    def combine_national(self):
        """Combine national totals"""
        self.merged = pd.concat(self.timeseries)
        print(self.merged)
        self.merged['Datum'] = pd.to_datetime(self.merged['Datum'])
        self.get_populations()
        self.merged = self.merged.set_index('Datum')
        self.merged.sort_index(inplace=True)
        print(self.merged)
        for country in self.cc:
            self.merged.loc[(self.merged.country == country), 'population'] \
                = self.national_populations[country] * 10
        self.merged['gpd-pc'] = self.merged['Aantal'] / self.merged['population']
        self.merged['radaily_pc'] = self.merged.groupby('country',
                                                        sort=False)['gpd-pc'] \
            .transform(lambda x: x.rolling(7, 1).mean())

    def get(self):
        """Return the data set"""
        return self.merged

    def get_populations(self):
        """National populations for the calculations that need it"""
        self.national_populations = pd.read_csv('data/populations.csv',  delimiter=',',
                                                index_col=0, header=None, squeeze=True).to_dict()

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
        dataframe['weekly'] = dataframe.groupby('Gemeentecode',
                                                 sort=False)['Aantal'] \
            .transform(lambda x: x.rolling(7).sum())
        dataframe['radaily_pc'] = dataframe['radaily'] / dataframe['pop_pc']
        dataframe['weekly_pc'] = dataframe['weekly'] / dataframe['pop_pc']
        if self.options.startdate is not None:
            dataframe = dataframe.query(f'{self.options.startdate} <= Datum')
        if self.options.enddate is not None:
            dataframe = dataframe.query(f'Datum <= {self.options.enddate}')
        print('Finished calculating combined data')
        self.merged = dataframe

    def parse_countries(self, country_str):
        """Sort out country data"""
        all = ['nl', 'sco', 'eng', 'wal', 'ni', 'be', 'de']
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
            if 'bel' in country:
                country = 'be'
            if 'ger' in country:
                country = 'de'
            ret.append(country)
        self.cc = ret
        self.countries = list(set(all) - set(ret))
        self.description = '_'.join(ret)

    def project_for_date(self, date):
        """Project infections per Gemeente and make league table"""
        if date is None:
            date = self.merged.index.max().strftime('%Y%m%d')
        datemax = datetime.datetime.strptime(date, '%Y%m%d')
        datemin = (datemax - timedelta(days=4)).strftime('%Y%m%d')
        self.merged = self.merged.query(f'{datemin} <= Datum <= {date}')
        self.merged = self.merged.groupby(['Gemeentecode']) \
            .agg({'Aantal': 'sum', 'Gemeentenaam': 'first',
                  'pop_pc': 'first', 'population': 'first', 'country': 'first'})
        self.merged['percapita'] = self.merged['Aantal'] / self.merged['pop_pc']
        self.merged.sort_values(by=['percapita'], ascending=False, inplace=True)
        print(self.merged.head(20))


class Timeseries:
    """Abstract class for timeseries"""

    def __init__(self, process=True):
        self.merged = None
        print(process)
        if process:
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


class BETimeseries(Timeseries):
    """Belgium data"""

    def __init__(self, process=True):
        """Init"""
        Timeseries.__init__(self, process)

    def national(self):
        """Get national totals"""
        dataframe = pd.read_csv('data/belgiumt.csv',
                                delimiter=',')
        dataframe.dropna(inplace=True)
        dataframe.rename(columns={'CASES': 'Aantal', 'DATE': 'Datum'}, inplace=True)
        dataframe = dataframe.groupby(['Datum']).agg({'Aantal': 'sum'})
        dataframe = dataframe.reset_index()
        dataframe = dataframe.assign(country='be')
        return dataframe

    def get_source_data(self):
        """Get BE source data for infections"""
        dataframe = pd.read_csv('data/belgium.csv', delimiter=',')
        dataframe.dropna(inplace=True)
        dataframe['CASES'] = dataframe['CASES'].replace(['<5'], '0')
        dataframe.rename(columns={'CASES': 'Aantal',
                                  'NIS5': 'Gemeentecode',
                                  'DATE': 'Datum',
                                  'TX_DESCR_NL': 'Gemeentenaam'}, inplace=True)
        dataframe.drop(columns=['TX_DESCR_FR', 'TX_ADM_DSTR_DESCR_NL', 'TX_ADM_DSTR_DESCR_FR',
                                'PROVINCE', 'REGION'], inplace=True)
        dataframe['Datum'] = pd.to_datetime(dataframe['Datum'])
        dataframe = self.resample(dataframe)
        dataframe = dataframe.set_index('Gemeentecode').dropna()
        merged = dataframe.join(self.pop)
        merged.index = merged.index.astype('int')
        # merged.reset_index(inplace=True)
        merged = merged.join(self.map)
        merged.reset_index(inplace=True)
        merged.rename(columns={'index': 'Gemeentecode'}, inplace=True)
        merged = merged.assign(country='be')
        self.merged = merged

    def resample(self, dataframe):
        """Timeseries is incomplete, fill it in"""
        # Normally you would just resample but we have 1500 od gemeentes each needs a
        # completed dataseries or chorpleths will look very odd
        idx = pd.date_range(min(dataframe.Datum), max(dataframe.Datum))
        gems = list(set(dataframe['Gemeentecode'].values))
        newdata = []
        for gem in gems:
            gemdf = dataframe[dataframe['Gemeentecode'] == gem]
            #gemdf.set_index(gemdf.Datum, inplace=True)
            default = self.get_row(gemdf.loc[gemdf['Gemeentecode'] == gem])
            gemdf['strdate'] = gemdf['Datum'].dt.strftime('%Y-%m-%d')
            for date in idx:
                fdate = date.strftime('%Y-%m-%d')
                if fdate not in gemdf['strdate'].values:
                    newdata.append({'Datum': date,
                                    'Gemeentecode': default['Gemeentecode'],
                                    'Gemeentenaam': default['Gemeentenaam'],
                                    'Aantal': default['Aantal']
                                    })
                else:
                    row = gemdf.loc[gemdf['Datum'] == date]
                    newdata.append({'Datum': date,
                                    'Gemeentecode': row['Gemeentecode'].values[0],
                                    'Gemeentenaam': row['Gemeentenaam'].values[0],
                                    'Aantal': int(row['Aantal'].values[0])
                                    })
        return pd.DataFrame(newdata)

    def get_row(self, series):
        """Return one row"""
        return {'Datum': series['Datum'].values[0],
                'Gemeentecode': series['Gemeentecode'].values[0],
                'Gemeentenaam': series['Gemeentenaam'].values[0],
                'Aantal': series['Aantal'].values[0]
                }

    def get_pop(self):
        """Fetch the Population figures for BE"""
        pop = pd.read_csv('data/bepop.csv', delimiter=',')
        pop = pop.set_index('Gemeentecode')
        self.pop = pop

    def get_map(self):
        """Get BE map data"""
        map_df = gpd.read_file('maps/BELGIUM_-_Municipalities.shp')
        map_df.rename(columns={'CODE_INS': 'Gemeentecode',
                               'ADMUNADU': 'Gemeentenaam'}, inplace=True)
        map_df['Gemeentecode'] = map_df['Gemeentecode'].astype('int')
        map_df.drop(columns=['Gemeentenaam'], inplace=True)
        map_df = map_df.set_index('Gemeentecode')
        self.map = map_df


class NLTimeseries(Timeseries):
    """Dutch Timeseries"""

    def __init__(self, process=True):
        """Init"""
        Timeseries.__init__(self, process)

    def national(self):
        """Get national totals"""
        dataframe = pd.read_csv('../CoronaWatchNL/data/rivm_NL_covid19_national.csv',
                                delimiter=',')
        dataframe = dataframe[dataframe['Type'] == 'Totaal']
        dataframe = dataframe.assign(country='nl')
        dataframe['Aantal'] = dataframe['Aantal'] - dataframe['Aantal'].shift(1)
        return dataframe

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

    def __init__(self, process=True):
        """Init"""
        Timeseries.__init__(self, process)

    def national(self):
        """Use national totals"""
        dataframe = pd.read_csv('data/ukt.csv')
        dataframe.rename(columns={"newCasesBySpecimenDate": "Aantal", 'date': 'Datum',
                                  'areaCode': 'Gemeentecode'}, inplace=True)
        dataframe.loc[(dataframe.Gemeentecode.astype(str).str.startswith('S')), 'country'] = 'sco'
        dataframe.loc[(dataframe.Gemeentecode.astype(str).str.startswith('W')), 'country'] = 'wal'
        dataframe.loc[(dataframe.Gemeentecode.astype(str).str.startswith('E')), 'country'] = 'eng'
        dataframe.loc[(dataframe.Gemeentecode.astype(str).str.startswith('N')), 'country'] = 'ni'
        return dataframe

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


class DETimeseries(Timeseries):
    """DE Timeseries"""

    def __init__(self, process=True):
        """Init"""
        Timeseries.__init__(self, process)

    def get_pop(self):
        """Fetch the population figures for the DE"""
        dataframe = pd.read_csv('data/depop.csv')
        dataframe = dataframe.set_index("Gemeentenaam")
        self.pop = dataframe

    def get_source_data(self):
        """Get DE source data for infections"""
        dataframe = pd.read_excel(
            'data/germany.xlsx', sheet_name='BL_7-Tage-Fallzahlen', skiprows=[0, 1])
        # Rename columns
        dataframe.rename(columns={'Unnamed: 0': 'Gemeentenaam'}, inplace=True)
        dataframe = dataframe.set_index('Gemeentenaam')
        dataframe = dataframe.T
        transform = []
        for index, row in dataframe.iterrows():
            for region in row.keys():
                transform.append({'Datum': row.name, 'Aantal': row[region], 'Gemeentenaam': region})
        dataframe = pd.DataFrame(transform)
        dataframe['Datum'] = pd.to_datetime(dataframe['Datum'])
        dataframe['Gemeentecode'] = dataframe['Gemeentenaam']
        dataframe = dataframe.set_index('Gemeentenaam')
        merged = dataframe.join(self.map)
        merged = merged.join(self.pop)
        merged = merged.assign(country='de')
        merged.dropna(inplace=True)
        self.merged = merged

    def get_map(self):
        """Get DE Map Data"""
        map_df = gpd.read_file('maps/germany.geojson')
        map_df.rename(columns={'name': 'Gemeentenaam'}, inplace=True)
        map_df = map_df.set_index("Gemeentenaam")
        self.map = map_df
