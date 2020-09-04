from uk_covid19 import Cov19API
import pandas as pd

endpoint = 'https://api.coronavirus.data.gov.uk/v1/data?'

england_only = [
    'areaType=nation',
    'areaName=England'
]

MUNICIPAL = 'data/uk_areas.csv'
# LTLA17CD,LTLA17NM,UTLA17CD,UTLA17NM,FID
## {'\ufeffLTLA17CD': 'E06000001', 'LTLA17NM': 'Hartlepool', 'UTLA17CD': 'E06000001', 'UTLA17NM': 'Hartlepool', 'FID': '1'}

england_only = [
    'areaType=ltla',
    #'areaName=E06000001'
]
cases_and_deaths = {
    "date": "date",
    "areaName": "areaName",
    "areaCode": "areaCode",
    "cumCasesBySpecimenDate": "cumCasesBySpecimenDate"
}
api = Cov19API(filters=england_only, structure=cases_and_deaths)
api.get_csv(save_as="data/uk.csv")
