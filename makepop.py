# Dumb noddy to create a belgian population file

import openpyxl
import pandas as pd

dfs = pd.read_excel('data/TF_SOC_POP_STRUCT_2016.xlsx')
dfs = dfs.groupby(['CD_MUNTY_REFNIS']).agg(sum)

columns = {'MS_POPULATION': 'population'}
dfs.rename(columns=columns, inplace=True)
print(dfs)
columns2 = ['CD_DSTR_REFNIS',  'CD_PROV_REFNIS',
            'CD_RGN_REFNIS',  'CD_CIV_STS',
            'CD_AGE', 'CD_YEAR']
dfs.drop(columns=columns2, inplace=True)
dfs.to_csv('data/bepop.csv')
