"""Read in, format and calculate the timeseries"""
import pandas as pd


class Population:
    """Dumb abstract class for specific country populations"""

    def __init__(self, timeseries):
        self.timeseries = timeseries
        self.gemmap = None
        self.read()

    def get_map(self):
        """Return the merged dataframe"""
        return self.gemmap

    def read(self):
        """Read in raw data and convert to dataframe"""


class PopulationNL(Population):
    """The Netherlands"""

    DATA = 'data/Regionale_kerncijfers_Nederland_31082020_181423.csv'

    def read(self):
        """Read in raw data and convert to dataframe"""
        dataframe = pd.read_csv(self.DATA,  delimiter=';')
        df2 = self.timeseries.get_maps()
        self.gemmap = dataframe.set_index("Regio's").join(
            self.timeseries.gemsdf.set_index('name'))
        self.gemmap = self.gemmap.dropna()
        # The joining columns columns must be the same type
        self.gemmap = self.gemmap.astype({'code': int})
        self.gemmap = df2.set_index("Gemnr").join(
            self.gemmap.set_index('code'))


class PopulationUK(Population):
    """United Kingdom"""

    DATA = 'data/ukpop4.csv'

    def read(self):
        df2 = self.timeseries.get_maps()
        dataframe = pd.read_csv(self.DATA,  delimiter=',')
        dataframe = dataframe.groupby(['ladcode20']).agg(sum)
        dataframe.to_csv('data/popagg.csv')
        self.gemmap = df2.set_index("lad17cd").join(dataframe)
        self.gemmap.rename(columns={"population_2019": "population"}, inplace=True)
        print(self.gemmap['population'])

    def read2(self):
        """Read in raw data and convert to dataframe"""
        dataframe = pd.read_csv(self.DATA,  delimiter=';')
        df2 = self.timeseries.get_maps()
        dataframe = dataframe[dataframe['AGE GROUP'].isin(['All ages'])]
        interesting = ['CODE', 'AREA', '2018']
        dataframe = dataframe[interesting]
        self.gemmap = df2.set_index("lad17cd").join(dataframe.set_index('CODE'))
        self.gemmap.rename(columns={"2018": "population"}, inplace=True)
