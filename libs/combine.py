"""Store the data in a nice big dataframe"""
import sys
from datetime import datetime, timedelta
import pandas as pd
import geopandas as gpd
import numpy as np


class Combine:
    """Combine defined countries together"""

    THE_EU = [ 'Austria', 'Italy', 'Belgium', 'Latvia',
               'Bulgaria', 'Lithuania', 'Croatia',
               'Luxembourg', 'Cyprus', 'Malta',
               'Czechia', 'Netherlands', 'Denmark',
               'Poland', 'Estonia', 'Portugal',
               'Finland', 'Romania', 'France',
               'Slovakia', 'Germany', 'Slovenia',
               'Greece', 'Spain', 'Hungary',
               'Sweden', 'Ireland' ]

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
        self.get_populations()
        self.countries_long = {'nl': 'The Netherlands', 'sco': 'Scotland', 'eng': 'England',
                               'wal': 'Wales', 'ni': 'Northern Ireland'}
        self.jhu = JHU(self)

    def judat(self):
        """Dumb helper for another library"""
        self.timeseries.append(NLTimeseries(False).national(False))
        self.combine_national(False)
        #self.merged['Week'] = self.merged.index.strftime('%U')
        #self.merged = self.merged.groupby(['Week']) \
            #.agg({'Aantal': 'sum'})
        print(self.merged)

    def process(self):
        """Do it"""
        cumulative = False
        if self.options.pivot:
            cumulative = True
        for nation in self.cc:
            usejhu = True
            if self.options.nation:
                print(f'Processing National data {nation}')
                if nation in ['wal', 'sco', 'eng']:
                    self.timeseries.append(UKTimeseries(False).national(nation,cumulative))
                    usejhu = False
                if nation == 'nl':
                    self.timeseries.append(NLTimeseries(False).national(cumulative))
                    usejhu = False
                if usejhu:
                    self.timeseries.append(XXTimeseries(False,
                                    {nation: self.countries_long[nation]}).national(cumulative))
            else:
                print(f'Processing combined data {nation}')
                if nation in ['wal', 'sco', 'eng']:
                    self.timeseries.append(UKTimeseries(True).get_data())
                    usejhu = False
                if nation == 'nl':
                    self.timeseries.append(NLTimeseries(True).get_data())
                    usejhu = False
                if usejhu:
                    self.timeseries.append(XXTimeseries(True).get_data())
        if len(self.timeseries) == 0:
            print('No country Data to process')
            sys.exit()
        if self.options.pivot:
            self.combine_pivot()
            return
        if self.options.nation:
            self.combine_national()
            return
        self.get_combined_data()

    def combine_pivot(self):
        """Pivot data for pandas_alive"""
        print('Pivotting data')
        self.merged = pd.concat(self.timeseries)
        self.merged['Datum'] = pd.to_datetime(self.merged['Datum'])
        # So we can add it as an option later
        column = 'Overleden'
        # Convert to 100K instead of millions
        for country in self.cc:
            self.merged.loc[(self.merged.country == country), 'population'] \
                = self.national_populations[country] * 10
        # Per-Capita
        self.merged[column] = self.merged[column] / self.merged['population']

        self.merged = self.merged.pivot(index='Datum',
                                        columns='country',
                                        values=column).fillna(0)
        self.trim_data()

    def combine_national(self, trim=True):
        """Combine national totals"""
        self.merged = pd.concat(self.timeseries)
        self.merged['Datum'] = pd.to_datetime(self.merged['Datum'])
        self.merged = self.merged.set_index('Datum')
        self.merged.sort_index(inplace=True)
        for country in self.cc:
            self.merged.loc[(self.merged.country == country), 'population'] \
                = self.national_populations[country] * 10
        for column in ['Aantal', 'Ziekenhuisopname', 'Overleden']:
            if column not in self.merged.columns:
                continue
            pgpd = f"{column}-gpd"
            radaily = f"{column}-radaily"
            raweekly = f"{column}-raweekly"
            self.merged[pgpd] = self.merged[column] / self.merged['population']
            self.merged[radaily] = self.merged.groupby('country',
                                                       sort=False)[pgpd] \
                .transform(lambda x: x.rolling(7, 1).mean())
            self.merged[raweekly] = self.merged.groupby('country',
                                                        sort=False)[pgpd] \
                .transform(lambda x: x.rolling(7).sum())
        if(trim):
            self.trim_data()

    def trim_data(self):
        if self.options.startdate is not None:
            self.merged = self.merged.query(f'{self.options.startdate} <= Datum')
        if self.options.enddate is not None:
            self.merged = self.merged.query(f'Datum <= {self.options.enddate}')

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
        ret = []
        if country_str is None:
            country_list = self.countries_long.keys()
        else:
            country_list = country_str.split(',')
        if 'eu' in country_list:
            country_list.remove('eu')
            country_list += self.THE_EU
            print('Setting EU')
        for country in country_list:
            country = country.lower()
            count = None
            if 'nether' in country:
                count = 'nl'
            if 'scot' in country:
                count = 'sco'
            if 'eng' in country:
                count = 'eng'
            if 'wal' in country:
                count = 'wal'
            #if 'ni' in country:
            #    count = 'ni'
            if count is not None:
                ret.append(count)
            else:
                retcountry = self.jhu.get_country(country)
                if retcountry:
                    ret.append(retcountry)
        self.cc = ret
        self.countries = list(set(self.countries_long.keys()) - set(ret))
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


class Timeseries:
    """Abstract class for timeseries"""

    def __init__(self, process=True):
        self.merged = None
        self.cumulative = False
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

    def set_cumulative(self, value):
        """Daily or cumulative"""
        self.cumulative = value


class JHU:
    """Get data from John Hopkins"""

    JHD = '../COVID-19/csse_covid_19_data'

    def __init__(self, combined):
        """Init"""
        self.dataframe = None
        self.combined = combined
        self.load()

    def get_country(self, country):
        """Check Country is in JHU data"""
        row = self.dataframe.loc[self.dataframe['Combined_Key'] == country]
        if len(row) == 0:
            return False
        self.combined.countries_long[row['iso2'].values[0].lower()] = country
        self.combined.national_populations[row['iso2'].values[0].lower()] \
            = row['Population'].values[0]
        return row['iso2'].values[0].lower()

    def load(self):
        """Load JHU lookup table"""
        dataframe = pd.read_csv(f'{self.JHD}/UID_ISO_FIPS_LookUp_Table.csv',
                                delimiter=',')
        dataframe['Combined_Key'] = dataframe['Combined_Key'].str.lower()
        dataframe['Population'] = dataframe['Population'] / 1e6
        self.dataframe = dataframe


class XXTimeseries(Timeseries):
    """Generic JHU Data class"""

    # TODO: Duplicated code
    JHD = '../COVID-19/csse_covid_19_data'

    def __init__(self, process=True, country=None):
        """Init"""
        Timeseries.__init__(self, process)
        self.countrycode = list(country.keys())[0]
        self.country = country[self.countrycode]
        self.cumullative = False


    def national(self, cumulative):
        self.set_cumulative(cumulative)
        """Get columns"""
        timeseries = 'csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
        overleden = self.calculate(timeseries, 'Overleden')
        timeseries = 'csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
        aantal = self.calculate(timeseries, 'Aantal')
        aantal['Overleden'] = overleden['Overleden']
        return aantal.assign(country=self.countrycode)

    def calculate(self, timeseries, column):
        """Get national totals"""
        file = f'{self.JHD}/{timeseries}'
        dataframe = pd.read_csv(file, delimiter=',')
        dataframe['Country/Region'] = dataframe['Country/Region'].str.lower()
        row = dataframe.loc[dataframe['Country/Region'] == self.country]
        row = row.loc[row['Province/State'].isnull()]
        row = row.reset_index(drop=True)
        row.drop(columns=['Province/State', 'Lat', 'Long'], inplace=True)
        row.set_index('Country/Region', inplace=True)
        dataframe = row.T
        if not self.cumulative:
            dataframe[column] = dataframe[self.country] - dataframe[self.country].shift(1)
        else:
            dataframe[column] = dataframe[self.country]
        dataframe.drop(columns=[self.country], inplace=True)
        dataframe.dropna(inplace=True)
        dataframe = dataframe.reset_index()
        dataframe.rename(columns={'index': 'Datum'}, inplace=True)
        return dataframe


class BETimeseries(Timeseries):
    """Belgium data"""

    def __init__(self, process=True):
        """Init"""
        Timeseries.__init__(self, process)

    def national(self, cumulative):
        """Get national totals"""
        self.set_cumulative(cumulative)
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

    def national(self, cumulative):
        """Get national totals"""
        self.set_cumulative(cumulative)
        df1 = self.get_subtotal('Totaal', rename=False, cumulative=self.cumulative)
        df2 = self.get_subtotal('Overleden', rename=True, cumulative=self.cumulative)
        df3 = self.get_subtotal('Ziekenhuisopname', rename=True, cumulative=self.cumulative)
        dataframe = df1.merge(df2, on='Datum')
        dataframe = dataframe.merge(df3, on='Datum')
        dataframe = dataframe.assign(country='nl')
        #dataframe = pd.concat([df1,df2,df3])
        return dataframe

    def get_subtotal(self, typ, rename=True, cumulative=True):
        """Get national totals"""
        dataframe = pd.read_csv('../CoronaWatchNL/data/rivm_NL_covid19_national.csv',
                                delimiter=',')
        dataframe = dataframe[dataframe['Type'] == typ]
        dataframe.drop(columns=['Type'], inplace=True)
        if not cumulative:
            print('Cumulative')
            dataframe['Aantal'] = dataframe['Aantal'] - dataframe['Aantal'].shift(1)
        if rename:
            dataframe.rename(columns={"Aantal": typ}, inplace=True)
        dataframe = dataframe.fillna(0)
        dataframe['Datum'] = pd.to_datetime(dataframe['Datum'])
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

    def national(self, country, cumulative):
        """Use national totals"""
        self.set_cumulative(cumulative)
        dataframe = pd.read_csv('data/ukt.csv')
        if cumulative:
            dataframe.rename(columns={"cumCasesBySpecimenDate": "Aantal", 'date': 'Datum',
                                      'areaCode': 'Gemeentecode',
                                      'cumDeaths28DaysByPublishDate': 'Overleden'}, inplace=True)
        else:
            dataframe.rename(columns={"newCasesBySpecimenDate": "Aantal", 'date': 'Datum',
                                      'areaCode': 'Gemeentecode',
                                      'newDeaths28DaysByPublishDate': 'Overleden'}, inplace=True)
        dataframe.loc[(dataframe.Gemeentecode.astype(str).str.startswith('S')), 'country'] = 'sco'
        dataframe.loc[(dataframe.Gemeentecode.astype(str).str.startswith('W')), 'country'] = 'wal'
        dataframe.loc[(dataframe.Gemeentecode.astype(str).str.startswith('E')), 'country'] = 'eng'
        dataframe.loc[(dataframe.Gemeentecode.astype(str).str.startswith('N')), 'country'] = 'ni'
        dataframe = dataframe[dataframe['country'] == country]
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
