import pandas as pd


class Population(object):

    DATA = 'data/Regionale_kerncijfers_Nederland_31082020_181423.csv'

    def __init__(self, ts):
        self.ts = ts
        self.read()

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

    def get_map(self):
        return self.gemmap
