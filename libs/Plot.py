"""Plotting routines"""
import os
import glob
import imageio
import matplotlib.pyplot as plt


class Plot:
    """ Create the individual plots which will
        later become the animation
        """

    FIGURES = 'figures3/'

    def __init__(self, ts):
        self.timeseries = ts
        plt.style.use('fivethirtyeight')
        self.cmap = 'Oranges'
        files = glob.glob(self.FIGURES + '*.png')
        for file in files:
            os.remove(file)
        self.vmin, self.vmax = 0, self.timeseries.get_max()

    def make_frames(self):
        """Create all the frames for each date in the timeseries"""
        count = 9999
        for date in sorted(self.timeseries.get_merged().columns):
            if date.startswith('2020-'):
                self.do_plot(date)
                count -= 1
            if count < 0:
                break

    def do_plot(self, date):
        """Create a single frame for a given date"""
        print(date)
        fig, axis = plt.subplots(1, figsize=(6, 6))
        self.timeseries.get_merged().plot(column=date, cmap=self.cmap, linewidth=0.8,
                                          ax=axis, edgecolor='0.8', legend=True, vmax=self.vmax)
        axis.axis('off')
        plt.title('%s %s' % (self.timeseries.get_cc(),  date))
        plt.figtext(0.5, 0.05, "Cumulative confirmed Cases per 100.000 inhabitants", ha="center",
                    fontsize=10, bbox={"facecolor": "white", "alpha": 0.5, "pad": 5})
        plt.savefig('figures3/%s.png' % date)
        plt.close(fig)

    def animate(self):
        """Create the animation
           This can be also done using Malibplot but this worked better for me
           """
        images = []
        directory = 'figures3/'
        for filename in os.listdir(directory):
            if filename.endswith(".png"):
                images.append(os.path.join(directory, filename))
        idata = []
        for i in sorted(images):
            idata.append(imageio.imread(i))
        filename = '%s_choropleth.mp4' % self.timeseries.get_cc()
        imageio.mimsave(filename, idata)
