# Covidanimate
Just some visualisations of the spread of covid in NL per Gemmeente or in the UK by Local Area (ltla)

The figures used are confirmed cases per 100K population in a specific Area.

If you want to play with it you will need a check out of CoronaWatchNL (for the NL data).  UK data is in the repo (see the notes about scrapeuk below)
https://github.com/J535D165/CoronaWatchNL

This is a collation of many data sources that is marvellously compiled and maintained by the University of Utrecht.

sh ./update.sh will update the data sources (assuemes you have CoronaWatchNL cloned)

Is written in python 3.8

##Countries
England
Wales
Scotland
Northern Ireland
Netherlands
Belgium

##Animated choropleth (local areas)

animate.py -a -c 'country'

##Local Area graphs

animate.py -g -r 'list of local areas'
eg.
animate.py -g -r 'Amsterdam,Rotterdam,Liverpool,Leeds'

##National graphs
animate.py -n -c 'countries'
eg.
animate.py -n -c 'Netherlands,Belgium'

##Animated National Graphs
animate.py -n -a -c 'countries'
eg.
animate.py -n -a -c 'Netherlands,Belgium'


