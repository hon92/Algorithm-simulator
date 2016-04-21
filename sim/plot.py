import gtk
import matplotlib.pyplot as plt
from matplotlib import style
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
from gui import statistics
style.use("fivethirtyeight")

class PlotStatistics(statistics.Statistics):
    def __init__(self, sim_widget):
        statistics.Statistics.__init__(self)
        self.sim_widget = sim_widget

    def create_properties(self):
        sim_time = self.sim_widget.simulation.env.now
        nodes_count = len(self.sim_widget.simulation.graph.nodes)
        self.add_property("sim_time", "Simulation time:", sim_time, self.sim_widget.statistics)

        for p in self.sim_widget.simulation.processes:
            display = "Process {0}:".format(p.id)
            val = " Calculated:{0}".format(p.edges_calculated)
            self.add_property("p{0}".format(p.id), display, val, self.sim_widget.statistics) 
        self.add_property("nodes_count", "Nodes count:", nodes_count, self.sim_widget.statistics)


class Plot():
    def __init__(self, fig):
        self.fig = fig

    def set_data(self, xdata, ydata, update = False):
        pass

    def redraw(self):
        pass

    def get_title(self):
        return ""

    def get_xlabel(self):
        return "x"

    def get_ylabel(self):
        return "y"

    def dispose(self):
        pass


class MemoryUsagePlot():
    def __init__(self, fig):
        Plot.__init__(self, fig)

    def get_xlabel(self):
        return "steps"

    def get_ylabel(self):
        return "size"

    def get_title(self):
        return "Memory usage"

class CalculatedTimePlot():
    def __init__(self, fig):
        Plot.__init__(self, fig)

    def get_xlabel(self):
        return ""

    def get_ylabel(self):
        return ""

    def get_title(self):
        return "Processes times"
    

class ProcessPlots():
    def __init__(self, fig):
        self.plots = []

    def add_plot(self, plot):
        self.plots.append(plot)



class SimPlotWidget(gtk.VBox):
    def __init__(self, simulation):
        gtk.VBox.__init__(self)
        self.simulation = simulation
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_TOP)
        self.figures = []
        self.id = 0
        self.colors = ["b", "g", "r", "c", "m", "y", "k"]
        self.plot_stats = PlotStatistics(self)

        def create_plot_widget(fill_fce):
            fig = plt.figure()
            ax = fig.gca()
            fill_fce(ax)
            vbox = gtk.VBox()
            canvas = FigureCanvas(fig)
            toolbar = NavigationToolbar(canvas, self.window)
            vbox.pack_start(canvas)
            vbox.pack_start(toolbar, False, False)
            self.figures.append(fig)
            return vbox

        def processes_calculated_plot(ax):
            def autolabel(rects):
                for rect in rects:
                    height = rect.get_height()
                    ax.text(rect.get_x() + rect.get_width() / 2.0, 1.05 * height,
                            '%f' % height,
                            ha='center', va='bottom')
            for process in simulation.processes:
                rects = ax.bar([process.id], [process.edges_calculated],
                               label = "process {0}".format(process.id),
                               color = self.colors[process.id])
                autolabel(rects)
            ax.set_title("Calculated nodes")
            ax.legend(prop = {"size":12})

        def memory_usage_plot(ax):
            ax.set_title("Memory uses")
            ax.set_xlabel("time")
            ax.set_ylabel("size")
            for process in simulation.processes:
                mon = process.monitor
                xdata, ydata = mon.get_data("memory_usage")
                ax.plot(xdata, ydata, marker = "o", label = "p {0}".format(process.id))
            ax.legend(prop = {"size":12})

        def create_statistics():
            vbox = gtk.VBox()
            hbox = gtk.HBox()
            hbox.pack_start(gtk.Label("Simulation results"), False, False)
            vbox.pack_start(hbox, False, False)
            return vbox

        def create_process_review(process):
            fig = plt.figure()
            ax1 = plt.subplot2grid((4, 1), (0, 0))
            ax2 = plt.subplot2grid((4, 1), (2, 0))
            ax3 = plt.subplot2grid((4, 1), (3, 0))
            ax4 = plt.subplot2grid((4, 1), (1, 0))

            ax1.set_title("Calculated")
            ax2.set_title("Memory push")
            ax3.set_title("Memory pop")
            ax4.set_title("Edges")
            
            ax1.set_xlabel("time")
            ax2.set_xlabel("step")
            ax3.set_xlabel("step")
            ax1.set_ylabel("count")
            ax2.set_ylabel("size")
            ax3.set_ylabel("size")
            ax4.set_xlabel("step")
            ax4.set_ylabel("edge")
            
            
            monitor = process.monitor
            xdata, ydata = monitor.get_data("edges_calculated")
            ax1.plot(xdata, ydata, marker = "o", label = "Edges")
            xdata, ydata = monitor.get_data("memory_push")
            ax2.plot(xdata, ydata, label = "process {0}".format(process.id))
            xdata, ydata = monitor.get_data("memory_pop")
            ax3.plot(xdata, ydata, label = "process {0}".format(process.id))
            xdata, ydata = monitor.get_data("edge_discovered")
            ax4.plot(xdata, ydata, marker = "o", label = "process {0}".format(process.id))
            ax1.legend(prop = {"size":12})
            ax2.legend(prop = {"size":12})
            ax3.legend(prop = {"size":12})
            vbox = gtk.VBox()
            canvas = FigureCanvas(fig)
            toolbar = NavigationToolbar(canvas, self.window)
            vbox.pack_start(canvas)
            vbox.pack_start(toolbar, False, False)
            self.figures.append(fig)
            plt.tight_layout(h_pad = -1.5, w_pad = 0.5)
            return vbox

        self.statistics = create_statistics()
        self.plot_stats.create_properties()
        self.notebook.append_page(self.statistics, gtk.Label("Results"))
        self.notebook.append_page(create_plot_widget(processes_calculated_plot), gtk.Label("Calculated"))
        self.notebook.append_page(create_plot_widget(memory_usage_plot), gtk.Label("Memory usage"))

        for p in self.simulation.processes:
            self.notebook.append_page(create_process_review(p), gtk.Label("Process {0}".format(p.id)))
        self.pack_start(self.notebook)
        self.show_all()

    def close(self):
        for fig in self.figures:
            plt.close(fig)
