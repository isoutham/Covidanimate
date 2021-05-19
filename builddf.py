from optparse import OptionParser
from libs.combine import Combine

def set_arguments(countries):
    parser = OptionParser()
    parser.add_option("-c", action="store", default=countries, dest="country")
    parser.add_option("-r", action="store_true", default=True, dest="nation")
    parser.add_option("-p", action="store_true", default=False, dest="pivot")
    parser.add_option("-s", action="store", default=None, dest="startdate")
    parser.add_option("-e", action="store", default=None, dest="enddate")
    (op, args) = parser.parse_args()
    return op

COUNTRIES = [
'India', 'Mexico', 'Brazil',
'United Kingdom', 'Norway',
'Austria', 'Italy', 'Belgium', 'Latvia',
'Bulgaria', 'Lithuania', 'Croatia',
'Luxembourg', 'Cyprus', 'Malta',
'Czechia', 'Netherlands', 'Denmark',
'Poland', 'Estonia', 'Portugal',
'Finland', 'Romania', 'France',
'Slovakia', 'Germany', 'Slovenia',
'Greece', 'Spain', 'Hungary',
'Sweden', 'Ireland'
]

options = set_arguments(','.join(COUNTRIES))
combined = Combine(options)
combined.parse_countries(options.country)
combined.process()
combined.get().to_csv("coviddata.csv")
