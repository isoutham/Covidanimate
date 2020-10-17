cd ../COVID-19
git pull
cd ../CoronaWatchNL
git pull
cd ../covid-19-uk-data
git pull
cd ../Covidanimate
# Belgium
curl -o data/belgium.csv https://epistat.sciensano.be/Data/COVID19BE_CASES_MUNI.csv
curl -o data/belgiumt.csv https://epistat.sciensano.be/Data/COVID19BE_CASES_AGESEX.csv
# Germany
curl -o data/germany.xlsx https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Daten/Fallzahlen_Kum_Tab.xlsx?__blob=publicationFile
# UK
python3.8 ./scrapeuk.py
