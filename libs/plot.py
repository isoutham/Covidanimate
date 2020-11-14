"""Produce plots"""
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib.animation as animation
import matplotlib.dates as mdates
from pandas.plotting import register_matplotlib_converters
from matplotlib.dates import DateFormatter
register_matplotlib_converters()


class Plot:
    """Plots"""

    def __init__(self, combined, regions):
        """Init"""
        self.combined = combined
        self.regions = regions
        self.countries = self.combined.countries
        self.dates = None
        self.fig = None
        self.axis = None

    def nations(self):
        """Graph country totals"""
        plt.style.use('dark_background')
        __, axis1 = plt.subplots(1, figsize=(14, 7))
        axis2 = None
        if self.combined.options.hospital:
            axis2 = axis1.twinx()
        plt.xlabel("Date")
        axis1.set_ylabel("Weekly Case per 100K inhabitants (RA)", color="w", fontsize=14)
        if axis2 is not None:
            axis2.set_ylabel("Weekly Hospital Admissions per 100K inhabitants (RA)",
                             color="w", fontsize=14)
            axis2.set_ylim(0,10)
        for nation in self.combined.cc:
            gem = self.combined.merged[self.combined.merged['country'] == nation]
            #gem.plot(y='Aantal-raweekly', label=self.combined.countries_long[nation], ax=axis)
            gem.plot(y='Aantal-raweekly',
                     label='Cases ' + self.combined.countries_long[nation],
                     ax=axis1, linestyle='solid')
            if axis2 is None:
                continue
            gem.plot(y='Ziekenhuisopname-raweekly',
                     label='Admissions ' + self.combined.countries_long[nation],
                     ax=axis2, linestyle='dotted')
            gem.plot(y='Overleden-raweekly',
                     label='Deaths ' + self.combined.countries_long[nation],
                     ax=axis2, linestyle='dotted')
        plt.grid(which='major', alpha=0.5)
        plt.grid(which='minor', alpha=0.2)
        axis1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), shadow=True, ncol=2)
        if axis2 is not None:
            axis2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.10), shadow=True, ncol=2)
        plt.tight_layout(pad=2)
        plt.savefig('national.png')

    def nations_animate(self):
        """Animate National graph"""
        self.dates = sorted(list(set(self.combined.merged.index)))
        self.fig = plt.figure(figsize=(10, 6))
        self.axis = self.fig.add_subplot(1, 1, 1)
        self.axis.axis(xmin=0, xmax=len(self.dates))
        self.axis.axis(ymin=0, ymax=1000)
        ani = animation.FuncAnimation(self.fig, self.animate_callback,
                                      frames=len(self.dates), interval=10)
        mp4writer = animation.writers['ffmpeg']
        writer = mp4writer(fps=5, metadata=dict(artist='Me'), bitrate=1800)
        ani.save('National_animation.mp4', writer=writer)

    def animate_callback(self, count):
        """Calback for the animated line graph"""
        enddate = self.dates[count].strftime('%Y%m%d')
        data = self.combined.merged.query(f'Datum <= {enddate}')
        self.axis.clear()
        for nation in self.combined.cc:
            gem = data[data['country'] == nation]
            xdata = gem.index
            ydata = gem['Aantal-raweekly']
            self.axis.plot(xdata, ydata, label=self.combined.countries_long[nation])
        date_form = DateFormatter("%b")
        self.axis.xaxis.set_major_formatter(date_form)
        self.axis.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Weekly Cases per 100,000 residents', fontsize=12)
        plt.title('Covid Cases', fontsize=14)
        #plt.legend(title='Nations', bbox_to_anchor=(.5, 1.05), fancybox=True, loc='upper center')
        plt.legend(title='Nations', fancybox=True, loc='upper left')

    def gemeente_graph(self):
        """Graphs by local municipality (gemeente)"""
        plt.style.use('dark_background')
        _, axis = plt.subplots(1, figsize=(14, 7))
        plt.xlabel("Date")
        plt.ylabel("Daily Cases per 100.000 - rolling 7 day mean")
        axis.set_title('Covid-19', color='white', fontsize=20)
        for gemeente in self.regions:
            gem = self.combined.merged[self.combined.merged['Gemeentenaam'] == gemeente]
            gem.plot(y='radaily_pc', label=gemeente, ax=axis)
        plt.grid(which='major', alpha=0.5)
        plt.grid(which='minor', alpha=0.2)
        plt.tight_layout(pad=2)
        plt.savefig('Gemeenten.png')

    def one_plot(self, merged, date):
        """Create one Chorpleth"""
        print("Creating a single frame for %s" % date)
        cmap = 'Oranges'
        plt.style.use('dark_background')
        fig, axis = plt.subplots(1, figsize=(7, 8.5))
        style_kwds = {
            'linewidth': 1,
            'markersize': 2,
            'facecolor': 'black',
            'edgecolor': 'black'
        }
        title = date.strftime('%d-%m-%Y')
        vmax = 400
        vmin = 0
        merged.plot(column='weekly_pc', vmax=vmax, vmin=vmin,
                    ax=axis, legend=True,
                    cmap=cmap, **style_kwds)
        axis.annotate(title,
                      xy=(0.1, .1),
                      xycoords='figure fraction',
                      horizontalalignment='left',
                      verticalalignment='top',
                      fontsize=16, color='white')
        axis.annotate('7 day infection totals per area',
                      xy=(0.1, .07),
                      xycoords='figure fraction',
                      horizontalalignment='left',
                      verticalalignment='top',
                      fontsize=8, color='white')
        axis.axis('off')
        # plt.figtext(0.3, 0.14, "Covid Confirmed Cases per 100.000 inhabitants",
        # ha="center",
        # fontsize=12, bbox={"facecolor": "white", "alpha": 0.5, "pad": 5})
        plt.tight_layout(pad=0.5)
        plt.savefig('figures5/%s.png' % date.strftime('%Y-%m-%d'))
        plt.close(fig)

    def make_frames(self):
        """Create a frame for all available dates"""
        for dat in list(set(self.combined.merged.index)):
            print(dat)
            if pd.isnull(dat):
                continue
            subset = self.get_one_date(dat)
            self.one_plot(subset, dat)

    def get_one_date(self, dat):
        """Data for one date (for animation)"""
        data = self.combined.merged[self.combined.merged.index == dat]
        return gpd.GeoDataFrame(data)
