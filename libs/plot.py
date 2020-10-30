"""Produce plots"""
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd


class Plot:
    """Plots"""

    def __init__(self, combined, regions):
        """Init"""
        self.combined = combined
        self.regions = regions
        self.countries = self.combined.countries

    def nations(self):
        """Graph country totals"""
        plt.style.use('dark_background')
        _, axis = plt.subplots(1, figsize=(14, 7))
        plt.xlabel("Date")
        plt.ylabel("Weekly Cases per 100.000 - rolling 7 day averge")
        for nation in self.combined.cc:
            gem = self.combined.merged[self.combined.merged['country'] == nation]
            print(gem)
            gem.plot(y='raweekly_pc', label=self.combined.countries_long[nation], ax=axis)
        plt.grid(which='major', alpha=0.5)
        plt.grid(which='minor', alpha=0.2)
        axis.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), shadow=True, ncol=2)
        plt.tight_layout(pad=2)
        plt.show()

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
        #title = date.strftime('%A %B %-d')
        title = date.strftime('%d-%m-%Y')
        #axis.set_title(title, loc='left', color='white',
                       #fontsize=20, fontname='Tahoma')
        #vmax=self.combined.get_max('weekly_pc') / 2
        vmax=400
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
