import pandas as pd


class Population(object):

    def __init__(self, ts):
        self.ts = ts
        self.read()

    def get_map(self):
        return self.gemmap


class PopulationNL(Population):

    DATA = 'data/Regionale_kerncijfers_Nederland_31082020_181423.csv'

    def __init__(self, ts):
        super(PopulationNL, self).__init__(ts)

    def read(self):
        df = pd.read_csv(self.DATA,  delimiter=';')
        df2 = self.ts.get_maps()
        self.gemmap = df.set_index("Regio's").join(
            self.ts.gemsdf.set_index('name'))
        self.gemmap = self.gemmap.dropna()
        # The joining columns columns must be the same type
        self.gemmap = self.gemmap.astype({'code': int})
        self.gemmap = df2.set_index("Gemnr").join(
            self.gemmap.set_index('code'))


class PopulationUK(Population):

    DATA = 'data/ukpop.csv'

    def __init__(self, ts):
        super(PopulationUK, self).__init__(ts)

    def read(self):
        df = pd.read_csv(self.DATA,  delimiter=';')
        df2 = self.ts.get_maps()
        df = df[df['AGE GROUP'].isin(['All ages'])]
        interesting = ['CODE', 'AREA', '2018']
        df = df[interesting]
        self.gemmap = df2.set_index("lad17cd").join(df.set_index('CODE'))
        self.gemmap = self.gemmap.dropna()
        self.gemmap.rename(columns={"2018": "population"}, inplace=True)
