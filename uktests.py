"""
Draw quick graph of UK testing
"""
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

# Data processing
dataframe = pd.read_csv('data/tests.csv',  delimiter=',')
# Group England, Wales, Scotland and NI by date
dataframe = dataframe.groupby(['date']).agg(sum)
# create a total of all test pillars
cumName = 'Total tests'
dataframe[cumName] = dataframe['cumPillarOneTestsByPublishDate'] + \
                     dataframe['cumPillarTwoTestsByPublishDate'] + \
                     dataframe['cumPillarThreeTestsByPublishDate']
# Convert to millions
dataframe[cumName] = dataframe[cumName] / 1e6

# Now plot the graph
plt.style.use('fivethirtyeight')
dataframe.index = pd.to_datetime(dataframe.index)
dataframe.head(len(dataframe) - 6).plot(y=cumName, linewidth=2)
ax = plt.gca()
plt.title('United Kingdom Tests')
ax.xaxis_date()
plt.xticks(size = 8, rotation='vertical')
plt.yticks(size = 8)
ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
plt.tight_layout()
plt.show()
