import gtk
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import style
style.use("fivethirtyeight")
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
from matplotlib import animation
from misc import colors

version = int(mpl.__version__.replace(".", ""))

if version >= 150:
    from cycler import cycler
    plt.rc("axes", prop_cycle = (cycler('color', colors.colors)))
else:
    plt.rc("axes", color_cycle = colors.colors)

class AbstractPlot():
    def __init__(self):
        self.figure = plt.figure()
        self.displayed = False
        self.disposed = False

    def get_widget(self):
        vbox = gtk.VBox()
        vbox.plot = self
        canvas = FigureCanvas(self.figure)
        vbox.pack_start(canvas)
        return vbox

    def get_widget_with_navbar(self, window):
        vbox = gtk.VBox()
        vbox.plot = self
        canvas = FigureCanvas(self.figure)
        vbox.pack_start(canvas)
        toolbar = NavigationToolbar(canvas, window)
        vbox.pack_start(toolbar, False, False)
        return vbox

    def get_figure(self):
        return self.figure

    def pre_process(self):
        pass

    def post_process(self):
        pass

    def draw_plot(self):
        pass

    def draw(self):
        if not self.displayed:
            self.pre_process()
            self.draw_plot()
            self.post_process()
            self.displayed = True

    def dispose(self):
        if not self.disposed:
            plt.close(self.figure)
            self.disposed = True

class AbstactSimplePlot(AbstractPlot):
    def __init__(self):
        AbstractPlot.__init__(self)
        self.axis = self.figure.gca()

    def pre_process(self):
        self.axis.set_title(self.get_title())
        self.axis.set_xlabel(self.get_xlabel())
        self.axis.set_ylabel(self.get_ylabel())
        self.axis.set_ymargin(0.2)

    def post_process(self):
        self.axis.legend(prop = {"size":12})
        self.figure.tight_layout(w_pad = -2.3)

    def draw_plot(self):
        pass

    def get_title(self):
        return ""

    def get_xlabel(self):
        return "x"

    def get_ylabel(self):
        return "y"

    def dispose(self):
        if not self.disposed:
            self.axis.cla()
            AbstractPlot.dispose(self)

class AbstractMultiPlot(AbstractPlot):
    def __init__(self):
        AbstractPlot.__init__(self)

    def add_subplot(self, index, width, height, xlabel = "", ylabel = "", title = ""):
        axis = self.figure.add_subplot(height, width, index)
        axis.set_xlabel(xlabel)
        axis.set_ylabel(ylabel)
        axis.set_title(title)
        axis.set_ymargin(0.2)
        return axis

    def dispose(self):
        if not self.disposed:
            for ax in self.figure.axes:
                ax.cla()
            AbstractPlot.dispose(self)

class MemoryUsagePlot(AbstactSimplePlot):
    def __init__(self, simulator):
        AbstactSimplePlot.__init__(self)
        self.simulator = simulator

    def draw_plot(self):
        for process in self.simulator.processes:
            mon = process.monitor
            xdata, ydata = mon.get_data("memory_usage")
            self.axis.plot(xdata, ydata, marker = "o", label = "p {0}".format(process.id))

    def get_xlabel(self):
        return "steps"

    def get_ylabel(self):
        return "size"

    def get_title(self):
        return "Memory usage"

class CalculatedBarPlot(AbstactSimplePlot):
    def __init__(self, simulator):
        AbstactSimplePlot.__init__(self)
        self.simulator = simulator

    def draw_plot(self):
        self.axis.set_prop_cycle(None)
        color_cycler = self.axis._get_lines.prop_cycler
        colors = []
        for _ in xrange(len(self.simulator.processes)):
            color_dict = next(color_cycler)
            hex_color = color_dict["color"]
            colors.append(hex_color)

        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                self.axis.text(rect.get_x() + rect.get_width() / 2.0, 1.05 * height,
                            '%f' % height,
                            ha='center', va='bottom')
                
        for process in self.simulator.processes:
            rects = self.axis.bar([process.id], [process.edges_calculated],
                                  label = "process {0}".format(process.id),
                                  color = colors[process.id])
            autolabel(rects)

    def get_xlabel(self):
        return ""

    def get_ylabel(self):
        return ""

    def get_title(self):
        return "Processes times"

class ProcessPlot(AbstractMultiPlot):
    def __init__(self, process):
        AbstractMultiPlot.__init__(self)
        self.process = process

    def pre_process(self):
        self.axis1 = self.add_subplot(1, 1, 4, "time", "count", "Calculated")
        self.axis2 = self.add_subplot(2, 1, 4, "step", "size", "Memory push")
        self.axis3 = self.add_subplot(3, 1, 4, "step", "size", "Memory pop")
        self.axis4 = self.add_subplot(4, 1, 4, "step", "edge", "Edges")
        for ax in self.figure.axes:
            ax.tick_params(labelsize=10)

    def draw_plot(self):
        label = "process {0}".format(self.process.id)
        monitor = self.process.monitor
        xdata, ydata = monitor.get_data("edges_calculated")
        self.axis1.plot(xdata, ydata, marker = "o", label = "Edges")
        xdata, ydata = monitor.get_data("memory_push")
        self.axis2.plot(xdata, ydata, label = label)
        xdata, ydata = monitor.get_data("memory_pop")
        self.axis3.plot(xdata, ydata, label = label)
        xdata, ydata = monitor.get_data("edge_discovered")
        self.axis4.plot(xdata, ydata, marker = "o", label = label)

    def post_process(self):
        self.axis1.legend(prop = {"size":12})
        self.axis2.legend(prop = {"size":12})
        self.axis3.legend(prop = {"size":12})
        self.axis4.legend(prop = {"size":12})
        self.figure.tight_layout(h_pad = -1.5, w_pad = 0.5)

    def get_title(self):
        return "Process id - {0}".format(self.process.id)

class VizualSimPlot(AbstractMultiPlot):
    def __init__(self):
        AbstractMultiPlot.__init__(self)

    def pre_process(self):
        font = {"fontsize":10}
        self.axis1 = self.add_subplot(1, 1, 4)
        self.axis1.set_title("Memory uses", fontdict = font)
        self.axis1.set_xlabel("size", fontdict = font)
        self.axis1.set_ylabel("time", fontdict = font)
        self.axis2 = self.add_subplot(2, 1, 4)
        self.axis2.set_title("Calculated", fontdict = font)
        self.axis2.set_xlabel("time", fontdict = font)
        self.axis2.set_ylabel("count", fontdict = font)
        self.axis3 = self.add_subplot(3, 1, 4)
        self.axis3.set_title("Edges discovered", fontdict = font)
        self.axis3.set_xlabel("time", fontdict = font)
        self.axis3.set_ylabel("count", fontdict = font)
        self.axis4 = self.add_subplot(4, 1, 4)
        self.axis4.set_title("Edges completed", fontdict = font)
        self.axis4.set_xlabel("time", fontdict = font)
        self.axis4.set_ylabel("count", fontdict = font)
        for ax in self.figure.axes:
            ax.tick_params(labelsize=8)

    def post_process(self):
        self.figure.tight_layout(w_pad = -2.3)

class AnimPlot(AbstractPlot):
    REFRESH_INTERVAL = 1000

    def __init__(self, plot, init_cb, anim_cb, frames):
        AbstractPlot.__init__(self)
        self.plot = plot
        self.anim_cb = anim_cb
        self.init_cb = init_cb
        self.frames = frames

    def get_widget(self):
        return self.plot.get_widget()

    def start(self):
        self.plot.draw()
        self.anim = animation.FuncAnimation(self.plot.figure,
                                            self.anim_cb,
                                            init_func = self.init_cb,
                                            interval = self.REFRESH_INTERVAL,
                                            frames = self.frames,
                                            repeat = False)
        self.get_figure().canvas.draw()

    def get_figure(self):
        return self.plot.get_figure()

    def dispose(self):
        AbstractPlot.dispose(self)

class VizualSimPlotAnim(AnimPlot):
    def __init__(self, init_cb, anim_cb, frames_gen):
        AnimPlot.__init__(self, VizualSimPlot(),
                          init_cb,
                          anim_cb,
                          frames_gen)
