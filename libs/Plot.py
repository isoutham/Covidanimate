import matplotlib.pyplot as plt
import os
import seaborn as sns
import glob
import imageio

class Plot(object):

    FIGURES = 'figures3/'

    def __init__(self, ts):
        self.ts = ts
        plt.style.use('fivethirtyeight')
        self.cmap = 'Oranges'
        files = glob.glob(self.FIGURES + '*.png')
        for f in files:
            os.remove(f)
        if self.ts.is_gemeente():
            self.vmin, self.vmax = 0, 500
        else:
            self.vmin, self.vmax = 0, 5000

    def make_frames(self):
        count = 9999
        for date in sorted(self.ts.get_merged().columns):
            if date.startswith('2020-'):
                self.do_plot(date)
                count -= 1
            if count < 0:
                break

    def do_plot(self, date):
        print(date)
        self.fig, self.ax = plt.subplots(1, figsize=(6, 6))
        self.ts.get_merged().plot(column=date, cmap=self.cmap, linewidth=0.8,
                                  ax=self.ax, edgecolor='0.8', legend=True, vmax=self.vmax)
        self.ax.axis('off')
        plt.title('The Netherlands ' + date)
        plt.savefig('figures3/%s.png' % date)
        plt.close(self.fig)

    def animate(self):
        images = []
        directory = 'figures3/'
        for filename in os.listdir(directory):
            if filename.endswith(".png"):
                images.append(os.path.join(directory, filename))
        idata = []
        for i in sorted(images):
            idata.append(imageio.imread(i))
        if self.ts.is_gemeente():
            fn = 'Gemeente_choropleth.mp4'
        else:
            fn = 'Provincie_choropleth.mp4'
        imageio.mimsave(fn, idata)
