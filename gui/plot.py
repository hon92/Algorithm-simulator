import gtk
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import style
style.use("fivethirtyeight")
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
from misc import colors as color_pallete

version = int(mpl.__version__.replace(".", ""))

if version >= 150:
    from cycler import cycler
    plt.rc("axes", prop_cycle = (cycler('color', color_pallete.colors)))
    plt.rc("legend", loc = "best", fontsize = 12)
else:
    plt.rc("axes", color_cycle = color_pallete.colors)
    plt.rc("legend", loc = "best", fontsize = 12)

def set_ax_color(ax):
    if version >= 150:
        ax.set_prop_cycle(cycler("color", color_pallete.colors))
    else:
        ax.set_color_cycle(color_pallete.colors)


class AbstractPlot():
    def __init__(self, figure):
        self.figure = figure
        self.displayed = False
        self.disposed = False

    def _get_canvas(self):
        canvas = FigureCanvas(self.figure)
        canvas.mpl_connect("pick_event", self.on_pick)
        return canvas

    def get_widget(self):
        vbox = gtk.VBox()
        vbox.plot = self
        vbox.pack_start(self._get_canvas())
        return vbox

    def get_widget_with_navbar(self, window):
        vbox = gtk.VBox()
        vbox.plot = self
        canvas = self._get_canvas()
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
            self.disposed = False

    def redraw(self):
        self.get_figure().canvas.draw_idle()

    def dispose(self):
        if not self.disposed:
            plt.close(self.figure)
            self.disposed = True
            self.displayed = False

    def on_pick(self, e):
        pass


class AbstactSimplePlot(AbstractPlot):
    def __init__(self, figure, title, xlabel, ylabel):
        AbstractPlot.__init__(self, figure)
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.axis = None
        self.lines_map = {}

    def pre_process(self):
        self.axis = self.create_axis()
        self.axis.set_title(self.get_title())
        self.axis.set_xlabel(self.get_xlabel())
        self.axis.set_ylabel(self.get_ylabel())
        self.axis.set_ymargin(0.2)
        self.axis.set_xmargin(0.2)

    def create_axis(self):
        return self.figure.gca()

    def post_process(self):
        self.map_leg_lines_to_axis(self.axis)
        self.figure.tight_layout(w_pad = -2.3)

    def get_title(self):
        return self.title

    def get_xlabel(self):
        return self.xlabel

    def get_ylabel(self):
        return self.ylabel

    def dispose(self):
        if not self.disposed:
            if self.axis:
                self.axis.cla()
            AbstractPlot.dispose(self)

    def on_pick(self, e):
        leg_line = e.artist
        if leg_line in self.lines_map:
            plot_line = self.lines_map[leg_line]
            visible = not plot_line.get_visible()
            marker = plot_line.get_marker()

            if e.mouseevent.button == 1:
                plot_line.set_visible(visible)
                if visible:
                    leg_line.set_alpha(1.0)
                else:
                    leg_line.set_alpha(0.2)
            elif e.mouseevent.button == 3:
                if marker == "o":
                    plot_line.set_marker("")
                else:
                    plot_line.set_marker("o")

        self.redraw()

    def map_leg_lines_to_axis(self, ax):
        leg = ax.get_legend()
        if not leg and len(ax.get_lines()):
            leg = ax.legend()

        if not leg:
            return

        axis_lines = []
        ax_lines = ax.get_lines()
        for l in ax_lines:
            axis_lines.append(l)

        for leg_line, ax_line in zip(leg.get_lines(), axis_lines):
            leg_line.set_picker(5)
            self.lines_map[leg_line] = ax_line


class AbstractMultiPlot(AbstractPlot):
    def __init__(self):
        AbstractPlot.__init__(self, plt.figure())
        self.plots = []

    def add_subplot(self, index, width, height, xlabel = "", ylabel = "", title = ""):
        self.plots.append(SubPlot(self.figure, title, xlabel, ylabel, index, width, height))

    def get_axis(self, plot_index):
        if plot_index < 0 or plot_index > len(self.plots):
            return None
        for p in self.plots:
            if p.get_index() == plot_index:
                return p.axis
        return None

    def on_pick(self, e):
        for p in self.plots:
            p.on_pick(e)

    def pre_process(self):
        for p in self.plots:
            p.pre_process()

    def post_process(self):
        for p in self.plots:
            p.post_process()

    def draw_plot(self):
        for p in self.plots:
            p.draw_plot()

    def dispose(self):
        if not self.disposed:
            for ax in self.figure.axes:
                ax.cla()
            AbstractPlot.dispose(self)


class SimplePlot(AbstactSimplePlot):
    def __init__(self, title, xlabel, ylabel):
        AbstactSimplePlot.__init__(self, plt.figure(1), title, xlabel, ylabel)


class SubPlot(AbstactSimplePlot):
    def __init__(self, figure, title, xlabel, ylabel, i, w, h):
        AbstactSimplePlot.__init__(self, figure, title, xlabel, ylabel)
        self.i = i
        self.w = w
        self.h = h

    def create_axis(self):
        return self.figure.add_subplot(self.h, self.w, self.i)

    def get_index(self):
        return self.i


class MemoryUsagePlot(SimplePlot):
    def __init__(self, simulation):
        SimplePlot.__init__(self, "Memory usage", "time", "storage size")
        self.simulation = simulation

    def draw_plot(self):
        entry_name = "memory_usage_time"
        processes = self.simulation.ctx.processes
        for process in processes:
            mm = process.ctx.monitor_manager
            mem_mon = mm.get_process_monitor(process.id, "MemoryMonitor")
            data = mem_mon.collect([entry_name])
            xdata = []
            ydata = []
            for d in data[entry_name]:
                xdata.append(d[0])
                ydata.append(d[1])
            self.axis.plot(xdata, ydata, marker = "o", label = "p {0}".format(process.id))


class CalculatedBarPlot(SimplePlot):
    def __init__(self, simulation):
        SimplePlot.__init__(self, "Processes times", "", "time")
        self.simulation = simulation

    def draw_plot(self):
        set_ax_color(self.axis)
        cc = color_pallete.new_color_cycler()
        processes = self.simulation.ctx.processes
        colors = []
        for _ in xrange(len(processes)):
            colors.append(next(cc))

        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                self.axis.text(rect.get_x() + rect.get_width() / 2.0, 1.05 * height,
                            "{0}".format(height),
                            ha='center', va='bottom')

        ind = np.arange(len(processes))
        width = 0.3
        time_values = []
        wait_values = []
        labels = []
        for process in processes:
            time = process.clock.get_time()
            waiting_time = process.clock.get_waiting_time()
            time_values.append(time)
            wait_values.append(waiting_time)
            labels.append("P{0}".format(process.id))

        rects = self.axis.bar(ind, time_values, width, color = "g", label = "Calculating time")
        autolabel(rects)
        rects1 = self.axis.bar(ind + width, wait_values, width, color = "r", label = "Waiting time")
        autolabel(rects1)
        self.axis.set_xticks(ind + width)
        self.axis.set_xticklabels(labels)


class ProcessesLifePlot(SimplePlot):
    def __init__(self, processes):
        SimplePlot.__init__(self, "Life of processes", "time", "processes")
        self.processes = processes

    def draw_plot(self):
        height = 2
        yspace = 2

        yticks = []

        for i, process in enumerate(self.processes):
            sim_time = process.ctx.env.now
            self.axis.set_xlim(0, sim_time)
            y = (i + 1) * height
            yticks.append(y + i*yspace + height / 2)
            self.axis.broken_barh([(0, sim_time)], (y + i*yspace, height), color = "g")
            mm = process.ctx.monitor_manager
            p_monitor = mm.get_process_monitor(process.id, "ProcessMonitor")
            data = []
            m_data = p_monitor.collect(["wait", "notify"])
            wait_data = m_data["wait"]
            notify_data = m_data["notify"]
            s = 0
            width = 0
            for wtime, in wait_data:
                s = wtime
                found_notify_evt = False
                for n_time, in notify_data:
                    if n_time > s:
                        width = n_time - s
                        found_notify_evt = True
                        break

                if not found_notify_evt:
                    width = sim_time - s
                data.append((s, width))
            self.axis.broken_barh(data, (y + i*yspace, height), color = "r")

        self.axis.set_yticks(yticks)
        self.axis.set_yticklabels(["Process {0}".format(p.id) for p in self.processes])

        red_patch = mpatches.Patch(color='red', label='waiting')
        green_patch = mpatches.Patch(color='green', label='working')
        self.axis.legend(handles=[red_patch, green_patch], loc = "best")


class ProcessPlot(AbstractMultiPlot):
    def __init__(self, process):
        AbstractMultiPlot.__init__(self)
        self.process = process

    def pre_process(self):
        self.add_subplot(1, 1, 4, "time", "storage size", "Memory")
        self.add_subplot(2, 1, 4, "time", "edge time", "Calculated")
        self.add_subplot(3, 1, 4, "time", "count", "Edges")

        AbstractMultiPlot.pre_process(self)
        for ax in self.get_figure().axes:
            ax.tick_params(labelsize=10)

    def draw_plot(self):
        mm = self.process.ctx.monitor_manager
        mem_monitor = mm.get_process_monitor(self.process.id, "MemoryMonitor")
        edge_monitor = mm.get_process_monitor(self.process.id, "EdgeMonitor")
        data = mem_monitor.collect(["push_time",
                                    "pop_time",
                                    "memory_usage_time"])

        push_data = data["push_time"]
        pop_data = data["pop_time"]
        mem_data = data["memory_usage_time"]

        xdata = []
        ydata = []
        for _, time, size in push_data:
            xdata.append(time)
            ydata.append(size)

        self.get_axis(1).plot(xdata, ydata, marker = "o", label = "Push")

        xdata = []
        ydata = []
        for _, time, size in pop_data:
            xdata.append(time)
            ydata.append(size)

        self.get_axis(1).plot(xdata, ydata, marker = "o", label = "Pop")

        xdata = []
        ydata = []
        for time, size in mem_data:
            xdata.append(time)
            ydata.append(size)

        self.get_axis(1).plot(xdata, ydata, marker = "o", label = "Memory")

        data = edge_monitor.collect(["edge_discovered",
                                     "edge_completed",
                                     "edge_calculated"])

        disc_data = data["edge_discovered"]
        calc_data = data["edge_calculated"]

        width = 0.1
        xdata = []
        ydata = []
        for time, _, edge_time, _, _, _ in calc_data:
            xdata.append(time)
            ydata.append(edge_time)

        self.get_axis(2).bar(xdata, ydata, width, color = "g", label = "Calculating time")

        xdata = []
        ydata = np.arange(len(disc_data))
        for time, _, _, _, _, _ in disc_data:
            xdata.append(time)

        self.get_axis(3).plot(xdata, ydata, marker = "o", label = "Discovered nodes")

        AbstractMultiPlot.draw_plot(self)

    def get_title(self):
        return "Process id - {0}".format(self.process.id)


class VizualSimPlot(AbstractMultiPlot):
    def __init__(self):
        AbstractMultiPlot.__init__(self)

    def pre_process(self):
        self.add_subplot(1, 1, 4, "time", "size", "Memory usage")
        self.add_subplot(2, 1, 4, "time", "count", "Calculated")
        self.add_subplot(3, 1, 4, "time", "count", "Edges discovered")
        self.add_subplot(4, 1, 4, "time", "count", "Edges completed")

        AbstractMultiPlot.pre_process(self)
        for ax in self.figure.axes:
            ax.tick_params(labelsize=8)


class AnimPlot():
    def __init__(self, plot):
        self.plot = plot

    def get_widget(self):
        return self.plot.get_widget()

    def get_widget_with_navbar(self, window):
        return self.plot.get_widget_with_navbar(window)

    def start(self):
        for pl in self.plot.plots:
            pl.dispose()
        self.plot.plots = []
        self.plot.pre_process()
        self.init_plot()
        self.plot.post_process()
        self.plot.displayed = True
        self.redraw()

    def update(self):
        self.update_frame()
        self.redraw()

    def redraw(self):
        self.plot.redraw()

    def init_plot(self):
        self.init()

    def get_figure(self):
        return self.plot.get_figure()

    def update_frame(self):
        pass

    def dispose(self):
        self.plot.dispose()


class VizualSimPlotAnim(AnimPlot):
    def __init__(self):
        AnimPlot.__init__(self, VizualSimPlot())
        self.processes = []
        self.marker = "o"
        self.enable_navbar = True
        self.unit_label = "time"
        self.show_time = True
        self.widget = None
        self.win = None

    def set_processes(self, processes):
        self.processes = processes

    def has_marker(self):
        return not self.marker == ""

    def has_navbar(self):
        return self.enable_navbar

    def get_unit(self):
        return self.unit_label

    def set_marker(self, marker_type):
        self.marker = marker_type
        fig = self.get_figure()
        axes = fig.axes
        for ax in axes:
            for l in ax.get_lines():
                l.set_marker(self.marker)

        self.redraw()

    def create_widget(self, window):
        if self.enable_navbar:
            self.win = window
            self.widget = self.get_widget_with_navbar(window)
        else:
            self.widget = self.get_widget()
        return self.widget

    def show_navbar(self, val):
        self.enable_navbar = val
        if self.widget:
            vbox = self.widget.get_parent()
            vbox.remove(self.widget)
            vbox.pack_start(self.create_widget(self.win))
            vbox.show_all()

    def set_unit(self, type):
        self.unit_label = type
        self.show_time = type == "time"
        self.update()

    def init(self):
        lines = []

        def init_ax(index, label):
            ax = self.plot.get_axis(index)
            line, = ax.plot([], [], label = label, marker = self.marker)
            return line

        for process in self.processes:
            label = "p {0}".format(process.id)
            for p in self.plot.plots:
                i = p.get_index()
                lines.append(init_ax(i, label))

        for ax in self.plot.get_figure().axes:
            set_ax_color(ax)
            ax.legend(prop = {"size": 10})
        return lines

    def update_frame(self):
        lines = []

        def update_ax(index, xdata, ydata, line, label):
            ax = self.plot.get_axis(index)
            ax.set_xlabel(self.get_unit())
            lines = ax.get_lines()
            l = lines[line - 1]
            l.set_data(xdata, ydata)
            lines.append(l)
            ax.relim()
            ax.autoscale_view()

        line = 1
        for process in self.processes:
            label = "p {0}".format(process.get_id())
            mm = process.get_monitor_manager()
            edge_monitor = mm.get_monitor("EdgeMonitor")
            memory_monitor = mm.get_monitor("MemoryMonitor")

            mem_usage_key = "memory_usage_time"

            if not self.show_time:
                mem_usage_key = "memory_usage_step"
            mem_data = memory_monitor.collect([mem_usage_key])
            mem_usage = mem_data[mem_usage_key]

            xdata = []
            ydata = []
            for x, y in mem_usage:
                xdata.append(x)
                ydata.append(y)

            update_ax(1, xdata, ydata, line, label)

            edge_data = edge_monitor.collect(["edge_discovered",
                                              "edge_calculated",
                                              "edge_completed"])

            edge_calc_data = edge_data["edge_calculated"]
            edge_disc_data = edge_data["edge_discovered"]
            edge_com_data = edge_data["edge_completed"]

            xdata = []
            ydata = []
            for sim_time, pr_time, pr_step, _ in edge_calc_data:
                if not self.show_time:
                    xdata.append(pr_step)
                else:
                    xdata.append(sim_time)
                ydata.append(pr_time)

            update_ax(2, xdata, ydata, line, label)

            xdata = []
            ydata = []
            i = 1
            for sim_time, pr_time, pr_step in edge_disc_data:
                if not self.show_time:
                    xdata.append(pr_step)
                else:
                    xdata.append(sim_time)
                ydata.append(i)
                i+=1

            update_ax(3, xdata, ydata, line, label)

            xdata = []
            ydata = []
            i = 1
            for sim_time, pr_time, pr_step in edge_com_data:
                if not self.show_time:
                    xdata.append(pr_step)
                else:
                    xdata.append(sim_time)
                ydata.append(i)
                i+=1

            update_ax(4, xdata, ydata, line, label)

            line += 1
        return lines

