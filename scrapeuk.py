"""
Grab data from the PHE API
"""
from uk_covid19 import Cov19API

england_only = [
    'areaType=nation',
    'areaName=England'
]

MUNICIPAL = 'data/uk_areas.csv'

ltla = [
    'areaType=ltla'
]
uk = [
    'areaType=nation'
]
cases = {
    "date": "date",
    "areaName": "areaName",
    "areaCode": "areaCode",
    "newCasesBySpecimenDate": "newCasesBySpecimenDate",
    "cumCasesBySpecimenDate": "cumCasesBySpecimenDate"
}
tests = {
    "date": "date",
    "areaName": "areaName",
    "cumPillarOneTestsByPublishDate": "cumPillarOneTestsByPublishDate",
    "cumPillarTwoTestsByPublishDate": "cumPillarTwoTestsByPublishDate",
    "cumPillarThreeTestsByPublishDate": "cumPillarThreeTestsByPublishDate"
}
#api = Cov19API(filters=uk, structure=tests)
#api.get_csv(save_as="data/tests.csv")

api = Cov19API(filters=ltla, structure=cases)
api.get_csv(save_as="data/uk.csv")
