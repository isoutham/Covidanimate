# Covidanimate
Just some visualisations of the spread of covid in NL per Gemmeente or in the UK by Local Area (ltla)

The figures used are confirmed cases per 100K population in a specific Area.

If you want to play with it you will need a check out of CoronaWatchNL (for the NL data).  UK data is in the repo (see the notes about scrapeuk below)
https://github.com/J535D165/CoronaWatchNL

This is a collation of many data sources that is marvellously compiled and maintained by the University of Utrecht.

scrapeuk.py will pull the data for the UK from the PHE API.
There is data in the data directory to use the program without scraping.

Just check it out into a parallel directory and run animate.py -n for NL animation or animate.py -u for the UK.

Is written in python 3.8
