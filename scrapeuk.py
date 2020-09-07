from uk_covid19 import Cov19API
import pandas as pd

endpoint = 'https://api.coronavirus.data.gov.uk/v1/data?'

england_only = [
    'areaType=nation',
    'areaName=England'
]

MUNICIPAL = 'data/uk_areas.csv'

england_only = [
    'areaType=ltla'
]
cases = {
    "date": "date",
    "areaName": "areaName",
    "areaCode": "areaCode",
    "newCasesBySpecimenDate": "newCasesBySpecimenDate",
    "cumCasesBySpecimenDate": "cumCasesBySpecimenDate"
}
api = Cov19API(filters=england_only, structure=cases)
api.get_csv(save_as="data/uk.csv")
