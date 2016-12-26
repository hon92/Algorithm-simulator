import gtk
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib import style
from gobject import gobject
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
        vbox.pack_start(NavigationToolbar(canvas, window), False)
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
        gobject.idle_add(self.get_figure().canvas.draw_idle)

    def dispose(self):
        if not self.disposed:
            plt.close(self.figure)
            self.disposed = True
            self.displayed = False


class AbstactSimplePlot(AbstractPlot):
    def __init__(self, figure, title, xlabel, ylabel):
        AbstractPlot.__init__(self, figure)
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.axis = None

    def pre_process(self):
        if self.axis is None:
            self.axis = self.create_axis()
        self.axis.set_title(self.get_title())
        self.axis.set_xlabel(self.get_xlabel())
        self.axis.set_ylabel(self.get_ylabel())
        self.axis.set_ymargin(0.2)
        self.axis.set_xmargin(0.2)

    def create_axis(self):
        return self.figure.gca()

    def post_process(self):
        self.legend_mapping(self.axis)
        self.figure.tight_layout()
        self.axis.relim()
        self.axis.autoscale_view()

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
        raise NotImplementedError()

    def legend_mapping(self, ax):
        raise NotImplementedError()


class AbstractMultiPlot(AbstractPlot):
    def __init__(self):
        AbstractPlot.__init__(self, plt.figure())
        self.plots = []

    def add_subplot(self, width, height, plot):
        index = len(self.plots) + 1
        plot.axis = self.figure.add_subplot(height, width, index)
        self.plots.append(plot)

    def get_axis(self, plot_index):
        if plot_index < 0 or plot_index > len(self.plots):
            return None
        return self.plots[plot_index].axis

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
    def __init__(self, title, xlabel, ylabel, fig = None):
        if fig is None:
            fig = plt.figure()
        AbstactSimplePlot.__init__(self, fig, title, xlabel, ylabel)


class LineSimplePlot(SimplePlot):
    def __init__(self, title, xlabel, ylabel, fig = None):
        SimplePlot.__init__(self, title, xlabel, ylabel, fig)
        self.lines_map = {}

    def on_pick(self, e):
        leg_line = e.artist
        plot_line = self.lines_map.get(leg_line)
        if plot_line is not None:
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

    def legend_mapping(self, ax):
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


class BarSimplePlot(SimplePlot):
    def __init__(self, title, xlabel, ylabel, fig = None):
        SimplePlot.__init__(self, title, xlabel, ylabel, fig)
        self.bar_map = {}

    def on_pick(self, e):
        rect = e.artist
        collection = self.bar_map.get(rect)
        if collection is not None:
            visible = not collection.get_visible()
            collection.set_visible(visible)
            if visible:
                rect.set_alpha(1.0)
            else:
                rect.set_alpha(0.2)
            self.redraw()

    def legend_mapping(self, ax):
        legend = self.axis.get_legend()

        for rect, collection in zip(legend.legendHandles, ax.collections):
            self.bar_map[rect] = collection

        for rect in legend.legendHandles:
            rect.set_picker(5)


class HistSimplePlot(SimplePlot):
    def __init__(self, title, xlabel, ylabel, fig = None):
        SimplePlot.__init__(self, title, xlabel, ylabel, fig)
        self.bar_map = {}

    def on_pick(self, e):
        rect = e.artist
        container = self.bar_map.get(rect)
        if container is not None:
            if rect.get_alpha() == 0.2:
                rect.set_alpha(1.0)
            else:
                rect.set_alpha(0.2)

            for r in container:
                visible = not r.get_visible()
                r.set_visible(visible)
            self.redraw()

    def legend_mapping(self, ax):
        legend = ax.get_legend()
        for rect in legend.legendHandles:
            rect.set_picker(5)
        for rect, container in zip(legend.legendHandles, ax.containers):
            self.bar_map[rect] = container


# plots for simulation detail
class MemoryUsagePlot(LineSimplePlot):
    def __init__(self, processes):
        LineSimplePlot.__init__(self, "Memory usage", "time", "memory usage")
        self.processes = processes

    def draw_plot(self):
        entry_name = "memory_usage"
        for process in self.processes:
            mm = process.ctx.monitor_manager
            mem_mon = mm.get_process_monitor(process.id, "MemoryMonitor")
            if not mem_mon:
                continue

            data = mem_mon.collect([entry_name])
            xdata = []
            ydata = []
            for d in data[entry_name]:
                xdata.append(d[0])
                ydata.append(d[1])
            self.axis.plot(xdata, ydata, label = "p {0}".format(process.id))

        process = self.processes[0]
        mm = process.ctx.monitor_manager
        mem_mon = mm.get_monitor("GlobalMemoryMonitor")
        if not mem_mon:
            return
        data = mem_mon.collect([entry_name])
        xdata = []
        ydata = []
        for d in data[entry_name]:
            xdata.append(d[0])
            ydata.append(d[1])
        self.axis.plot(xdata, ydata, label = "memory peak")


class StorageMemoryUsagePlot(LineSimplePlot):
    def __init__(self, processes):
        LineSimplePlot.__init__(self, "Storage memory usage", "time", "storage size")
        self.processes = processes

    def draw_plot(self):
        entry_name = "changed"
        for process in self.processes:
            mm = process.ctx.monitor_manager
            mem_mon = mm.get_process_monitor(process.id, "StorageMonitor")
            if not mem_mon:
                continue

            data = mem_mon.collect([entry_name])
            xdata = []
            ydata = []
            for d in data[entry_name]:
                xdata.append(d[0])
                ydata.append(d[1])
            self.axis.plot(xdata, ydata, label = "p {0}".format(process.id))

        pr = self.processes[0]
        mm = pr.ctx.monitor_manager
        gsm = mm.get_monitor("GlobalStorageMonitor")
        if gsm:
            data = gsm.collect([entry_name])
            xdata = []
            ydata = []
            for d in data[entry_name]:
                xdata.append(d[0])
                ydata.append(d[1])
            self.axis.plot(xdata, ydata, label = "memory peak")


class ProcessesLifePlot(BarSimplePlot):
    def __init__(self, processes):
        BarSimplePlot.__init__(self, "Life of processes", "time", "processes")
        self.processes = processes

    def draw_plot(self):
        height = 2
        yspace = 2
        yticks = []

        sim_time = self.processes[0].ctx.env.now
        for i, process in enumerate(self.processes):
            y = (i + 1) * height
            yticks.append(y + i*yspace + height / 2)
            ypos = (y + i * yspace, height)
            self.axis.broken_barh([(0, sim_time)],
                                  ypos,
                                  facecolor = "white",
                                  edgecolor = "white",
                                  alpha = 0.0)

            mm = process.ctx.monitor_manager
            edge_mon = mm.get_process_monitor(process.id, "EdgeMonitor")
            self.axis.broken_barh(self.get_edges_data(edge_mon),
                                  ypos,
                                  facecolor = "green",
                                  edgecolor = "white")

            p_monitor = mm.get_process_monitor(process.id, "ProcessMonitor")
            self.axis.broken_barh(self.get_waiting_data(p_monitor, sim_time),
                                  ypos,
                                  facecolor = "red",
                                  edgecolor = "red")

            com_monitor = mm.get_process_monitor(process.id, "CommunicationMonitor")
            self.axis.broken_barh(self.get_send_data(com_monitor),
                                  ypos,
                                  facecolor = "blue",
                                  edgecolor = "white")

        self.axis.set_xlim(0, sim_time)
        self.axis.set_yticks(yticks)
        self.axis.set_yticklabels(["Process {0}".format(p.id) for p in self.processes])

        handles = []
        handles.append(mpatches.Patch(color = 'green', label = 'working'))
        handles.append(mpatches.Patch(color = 'red', label = 'waiting'))
        handles.append(mpatches.Patch(color = 'blue', label = 'send'))
        self.axis.legend(handles = handles, loc = "best")

    def get_waiting_data(self, p_monitor, sim_time):
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
        return data

    def get_send_data(self, com_monitor):
        data = []
        m_data = com_monitor.collect(["send",
                                      "async_send"])
        async_send_data = [(d[0], d[3]) for d in m_data["async_send"]]
        send_data = [(d[0], d[3]) for d in m_data["send"]]
        data.extend(async_send_data)
        data.extend(send_data)
        return data

    def get_edges_data(self, edge_monitor):
        calc_data = edge_monitor.collect(["edge_calculated"])
        data = [(d[0] - d[3], d[3]) for d in calc_data["edge_calculated"]]
        return data

    def post_process(self):
        self.legend_mapping(self.axis)
        self.figure.tight_layout()
        self.axis.relim()
        self.axis.autoscale_view(True, True, False)

    def legend_mapping(self, ax):
        rects = ax.get_legend().legendHandles
        if len(rects) == 0:
            return
        for r in rects:
            r.set_picker(5)
        collections = ax.collections

        for r in rects:
            self.bar_map[r] = []
            for collection in collections:
                arr = collection.get_facecolor()
                c = r.get_facecolor()
                if c[0] == arr.item(0) and c[1] == arr.item(1) \
                    and c[2] == arr.item(2) and c[3] == arr.item(3):
                    self.bar_map[r].append(collection)

    def on_pick(self, e):
        rect = e.artist
        collections = self.bar_map.get(rect)
        if collections:
            for c in collections:
                visible = not c.get_visible()
                c.set_visible(visible)
                if visible:
                    rect.set_alpha(1.0)
                else:
                    rect.set_alpha(0.2)
            self.redraw()


class DiscoveredPlot(LineSimplePlot):
    def __init__(self, processes):
        LineSimplePlot.__init__(self, "Discovered nodes", "simulation time", "nodes discovered")
        self.processes = processes

    def draw_plot(self):
        for p in self.processes:
            mm = p.ctx.monitor_manager
            edge_mon = mm.get_process_monitor(p.id, "EdgeMonitor")
            if not edge_mon:
                continue
            entry_name = "edges_discovered_in_time"
            data = edge_mon.collect([entry_name])
            disc_data = data[entry_name]
            xdata = []
            ydata = []
            for sim_time, c in disc_data:
                xdata.append(sim_time)
                ydata.append(c)
            self.axis.plot(xdata, ydata, label = "p {0}".format(p.id))


class CummulativeSumPlot(LineSimplePlot):
    def __init__(self, processes):
        LineSimplePlot.__init__(self,
                                "Cummulative sum of discovered nodes",
                                "simulation time",
                                "nodes discovered")
        self.processes = processes

    def draw_plot(self):
        for p in self.processes:
            mm = p.ctx.monitor_manager
            edge_mon = mm.get_process_monitor(p.id, "EdgeMonitor")
            if not edge_mon:
                continue
            disc_cummulative_entry = "edges_discovered_cummulative"
            data = edge_mon.collect([disc_cummulative_entry])
            disc_cummulative_data = data[disc_cummulative_entry]

            xdata = []
            ydata = []
            for sim_time, s in disc_cummulative_data:
                xdata.append(sim_time)
                ydata.append(s)
            self.axis.plot(xdata, ydata, label = "p {0} cummulative sum".format(p.id))


class CalculatedPlot(HistSimplePlot):
    def __init__(self, processes):
        HistSimplePlot.__init__(self, "Calculating edges", "edge time", "edges count")
        self.processes = processes

    def draw_plot(self):
        num_step = 20
        color_cycler = color_pallete.new_color_cycler()
        legend = []
        for p in self.processes:
            mm = p.ctx.monitor_manager
            edge_mon = mm.get_process_monitor(p.id, "EdgeMonitor")
            if not edge_mon:
                continue

            entry_name = "edge_calculated"
            data = edge_mon.collect([entry_name])
            calc_data = data[entry_name]
            xdata = []

            for _, _, edge_time, _, _, _, _ in calc_data:
                xdata.append(edge_time)

            color = next(color_cycler)
            if len(xdata) != 0:
                min_v = min(xdata)
                max_v = max(xdata)
                if min_v == max_v:
                    bins_v = int(max_v)
                    bins = [bins_v]
                else:
                    bins = np.linspace(min_v, max_v, num_step)
            else:
                bins = [0]
                xdata = [0]
            self.axis.hist(xdata, bins = bins, histtype = 'bar', color = color)
            legend.append(mpatches.Patch(color=color, label = "p {0}".format(p.id)))

        self.axis.legend(handles=legend, loc = "best")


class ProcessMemoryUsagePlot(LineSimplePlot):
    def __init__(self, process):
        LineSimplePlot.__init__(self, "Memory usage", "time", "size")
        self.process = process

    def draw_plot(self):
        mm = self.process.ctx.monitor_manager
        mem_monitor = mm.get_process_monitor(self.process.id, "MemoryMonitor")
        if mem_monitor:
            self._memory_plots(mem_monitor)

        storage_monitor = mm.get_process_monitor(self.process.id, "StorageMonitor")
        if storage_monitor:
            self._storage_memory_plot(storage_monitor)

    def _memory_plots(self, mem_monitor):
        mem_entry = "memory_usage"

        data = mem_monitor.collect([mem_entry])
        mem_data = data[mem_entry]

        xdata = []
        ydata = []
        for time, size in mem_data:
            xdata.append(time)
            ydata.append(size)
        self.axis.plot(xdata, ydata, label = "Memory")

    def _storage_memory_plot(self, storage_monitor):
        push_entry = "push"
        pop_entry = "pop"
        change_entry = "changed"
        data = storage_monitor.collect([push_entry, pop_entry, change_entry])
        push_data = data[push_entry]
        pop_data = data[pop_entry]
        change_data = data[change_entry]

        xdata = []
        ydata = []
        for time, size in push_data:
            xdata.append(time)
            ydata.append(size)
        self.axis.plot(xdata, ydata, label = "Push")

        xdata = []
        ydata = []
        for time, size in pop_data:
            xdata.append(time)
            ydata.append(size)
        self.axis.plot(xdata, ydata, label = "Pop")

        xdata = []
        ydata = []
        for time, size in change_data:
            xdata.append(time)
            ydata.append(size)
        self.axis.plot(xdata, ydata, label = "Storage memory")


class ProcessCalculatedPlot(BarSimplePlot):
    def __init__(self, process):
        BarSimplePlot.__init__(self, "Calculated", "time", "edge time")
        self.process = process

    def draw_plot(self):
        mm = self.process.ctx.monitor_manager
        edge_monitor = mm.get_process_monitor(self.process.id, "EdgeMonitor")
        calc_edge_entry = "edge_calculated"
        data = edge_monitor.collect([calc_edge_entry])

        xdata = []
        ydata = []
        for time, _, edge_time, _, _, _, _ in data[calc_edge_entry]:
            xdata.append(time)
            ydata.append(edge_time)

        self.axis.vlines(xdata, [0], ydata, color = "green", label = "Calculating time")
        if len(xdata) and len(ydata) > 0:
            self.axis.set_xlim([0, xdata[-1] + 2])
            self.axis.set_ylim([0, max(ydata)])
        self.axis.legend(handles = [mpatches.Patch(color = "green", label = "edges")],
                         loc = "best")


class ProcessDiscoveredEdgesPlot(LineSimplePlot):
    def __init__(self, process):
        LineSimplePlot.__init__(self, "Discovered edges", "time", "edges count")
        self.process = process

    def draw_plot(self):
        mm = self.process.ctx.monitor_manager
        edge_monitor = mm.get_process_monitor(self.process.id, "EdgeMonitor")
        disc_edge_time_entry = "edges_discovered_in_time"
        disc_cummulative_entry = "edges_discovered_cummulative"

        data = edge_monitor.collect([disc_edge_time_entry,
                                     disc_cummulative_entry])
        cummulative_data = data[disc_cummulative_entry]
        disc_data = data[disc_edge_time_entry]
        xdata = []
        ydata = []
        for sim_time, count in disc_data:
            xdata.append(sim_time)
            ydata.append(count)
        self.axis.plot(xdata, ydata, label = "Discovered edges")

        xdata = []
        ydata = []
        for sim_time, s in cummulative_data:
            xdata.append(sim_time)
            ydata.append(s)
        self.axis.plot(xdata, ydata, label = "Cummulative sum")


class ProcessCommunicationPlot(LineSimplePlot):
    def __init__(self, process):
        LineSimplePlot.__init__(self, "Process communication", "time", "message size")
        self.process = process

    def draw_plot(self):
        mm = self.process.ctx.monitor_manager
        com_monitor = mm.get_process_monitor(self.process.id, "CommunicationMonitor")
        processes = self.process.ctx.processes
        send_entry = "send"
        receive_entry = "receive"
        asend_entry = "async_send"
        areceive_entry = "async_receive"
        data = com_monitor.collect([send_entry,
                                    receive_entry,
                                    asend_entry,
                                    areceive_entry])

        color_cycler = color_pallete.new_color_cycler()
        colors = []
        for _ in xrange(len(self.process.ctx.processes)):
            colors.append(next(color_cycler))

        legends = []
        self.max_x = 0
        self.max_y = 0

        def draw_entry(entry_name, label, linestyle):
            for p in processes:
                p_data = [(d[0], d[2]) for d in data[entry_name] if d[1] == p.id]
                xdata = []
                ydata = []
                for sim_time, size in p_data:
                    xdata.append(sim_time)
                    ydata.append(size)
                    if sim_time > self.max_x:
                        self.max_x = sim_time
                    if size > self.max_y:
                        self.max_y = size

                self.axis.vlines(xdata,
                                 [0],
                                 ydata,
                                 color = colors[p.id],
                                 label = entry_name,
                                 linestyle = linestyle)

                legends.append(mlines.Line2D([],
                                             [],
                                             color = colors[p.id],
                                             linestyle = linestyle,
                                             label = label.format(entry_name, p.id)))

        draw_entry(asend_entry, "{0} to p {1}", "solid")
        draw_entry(areceive_entry, "{0} from p {1}", "dashed")
        draw_entry(send_entry, "{0} to p {1}", "dashdot")
        draw_entry(receive_entry, "{0} from p {1}", "dotted")

        self.axis.set_xlim([0, self.max_x + 5])
        self.axis.set_ylim([0, self.max_y + 5])
        self.axis.legend(handles=legends, loc = "best")

    def legend_mapping(self, ax):
        legend = ax.get_legend()
        for line in legend.legendHandles:
            line.set_picker(5)

        for line, line_col in zip(legend.legendHandles, ax.collections):
            self.lines_map[line] = line_col

    def on_pick(self, e):
        line = e.artist
        line_col = self.lines_map.get(line)
        if line_col:
            visible = not line_col.get_visible()
            line_col.set_visible(visible)
            if visible:
                line.set_alpha(1.0)
            else:
                line.set_alpha(0.2)
            self.redraw()


class ProcessPlot(AbstractMultiPlot):
    def __init__(self, process):
        AbstractMultiPlot.__init__(self)
        self.process = process

    def pre_process(self):
        self.add_subplot(1, 1, 3, "simulation time", "storage size", "Memory usage")
        self.add_subplot(2, 1, 3, "time", "edge time", "Calculated")
        self.add_subplot(3, 1, 3, "simulation time", "edges count", "Discovered edges")

        AbstractMultiPlot.pre_process(self)
        for ax in self.get_figure().axes:
            ax.tick_params(labelsize=10)

    def draw_plot(self):
        mm = self.process.ctx.monitor_manager
        mem_monitor = mm.get_process_monitor(self.process.id, "MemoryMonitor")
        if mem_monitor:
            self._memory_plots(mem_monitor)

        storage_monitor = mm.get_process_monitor(self.process.id, "StorageMonitor")
        if storage_monitor:
            self._storage_memory_plot(storage_monitor)

        edge_monitor = mm.get_process_monitor(self.process.id, "EdgeMonitor")
        if edge_monitor:
            self._edge_plots(edge_monitor)

        AbstractMultiPlot.draw_plot(self)

    def get_title(self):
        return "Process id - {0}".format(self.process.id)

    def _memory_plots(self, mem_monitor):
        axis = self.get_axis(1)
        mem_entry = "memory_usage"

        data = mem_monitor.collect([mem_entry])
        mem_data = data[mem_entry]

        xdata = []
        ydata = []
        for time, size in mem_data:
            xdata.append(time)
            ydata.append(size)
        axis.plot(xdata, ydata, label = "Memory")

    def _storage_memory_plot(self, storage_monitor):
        axis = self.get_axis(1)
        push_entry = "push"
        pop_entry = "pop"
        change_entry = "changed"
        data = storage_monitor.collect([push_entry, pop_entry, change_entry])
        push_data = data[push_entry]
        pop_data = data[pop_entry]
        change_data = data[change_entry]

        xdata = []
        ydata = []
        for time, size in push_data:
            xdata.append(time)
            ydata.append(size)
        axis.plot(xdata, ydata, label = "Push")

        xdata = []
        ydata = []
        for time, size in pop_data:
            xdata.append(time)
            ydata.append(size)
        axis.plot(xdata, ydata, label = "Pop")

        xdata = []
        ydata = []
        for time, size in change_data:
            xdata.append(time)
            ydata.append(size)
        axis.plot(xdata, ydata, label = "Storage memory")

    def _edge_plots(self, edge_monitor):
        axis = self.get_axis(2)
        edge_axis = self.get_axis(3)
        calc_edge_entry = "edge_calculated"
        disc_edge_time_entry = "edges_discovered_in_time"
        disc_cummulative_entry = "edges_discovered_cummulative"

        data = edge_monitor.collect([calc_edge_entry,
                                     disc_edge_time_entry,
                                     disc_cummulative_entry])

        calc_data = data[calc_edge_entry]
        cummulative_data = data[disc_cummulative_entry]
        xdata = []
        ydata = []
        for time, _, edge_time, _, _, _ in calc_data:
            xdata.append(time)
            ydata.append(edge_time)

        axis.vlines(xdata, [0], ydata, color = "g", label = "Calculating time")
        if len(xdata) and len(ydata) > 0:
            axis.set_xlim([0, xdata[-1] + 2])
            axis.set_ylim([0, max(ydata)])

        disc_data = data[disc_edge_time_entry]
        xdata = []
        ydata = []
        for sim_time, count in disc_data:
            xdata.append(sim_time)
            ydata.append(count)
        edge_axis.plot(xdata, ydata, label = "Discovered edges")

        xdata = []
        ydata = []
        for sim_time, s in cummulative_data:
            xdata.append(sim_time)
            ydata.append(s)
        edge_axis.plot(xdata, ydata, label = "Cummulative sum")


# end plot for simulation detail


class SummaryBoxPlot(SimplePlot):
    def __init__(self, data, ticks, title, ylabel):
        SimplePlot.__init__(self, title, "", ylabel)
        self.data = data
        self.ticks = ticks

    def draw_plot(self):
        self.axis.boxplot(self.data)
        self.axis.set_xticklabels(self.ticks)

    def legend_mapping(self, ax):
        pass


class TimeSummaryPlot(SummaryBoxPlot):
    def __init__(self, data, ticks):
        SummaryBoxPlot.__init__(self, data, ticks, "Time summary", "time")


class MemorySummaryPlot(SummaryBoxPlot):
    def __init__(self, data, ticks):
        SummaryBoxPlot.__init__(self, data, ticks, "Memory summary", "memory")


class VisualSimPlot(AbstractMultiPlot):
    def __init__(self):
        AbstractMultiPlot.__init__(self)

    def pre_process(self):
        self.add_subplot(1, 3, LineSimplePlot("Memory usage", "time", "size", self.figure))
        self.add_subplot(1, 3, BarSimplePlot("Calculated", "time", "edge time", self.figure))
        self.add_subplot(1, 3, LineSimplePlot("Edges discovered", "time", "count", self.figure))

        AbstractMultiPlot.pre_process(self)
        for ax in self.figure.axes:
            ax.tick_params(labelsize=8)


class ScalabilityPlot(LineSimplePlot):
    def __init__(self, process_type, pr_min, pr_max, pr_step, ydata, yerr):
        title = "{0} - strong scalability".format(process_type)
        LineSimplePlot.__init__(self, title,"process count", "time")
        self.process_type = process_type
        self.pr_min = pr_min
        self.pr_max = pr_max
        self.pr_step = pr_step
        self.ydata = ydata
        self.yerr = yerr

    def draw_plot(self):
        self.axis.errorbar(np.arange(self.pr_min,
                                 self.pr_max,
                                 self.pr_step),
                           self.ydata,
                           yerr = self.yerr,
                           label = self.process_type,
                           elinewidth = 0.8)


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

    def init(self):
        pass


class VizualSimPlotAnim(AnimPlot):
    def __init__(self):
        AnimPlot.__init__(self, VisualSimPlot())
        self.processes = []
        self.marker = ""
        self.enable_navbar = True
        self.show_time = True
        self.widget = None
        self.win = None

    def set_processes(self, processes):
        self.processes = processes

    def has_marker(self):
        return not self.marker == ""

    def has_navbar(self):
        return self.enable_navbar

#     def get_unit(self):
#         return self.unit_label

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

    def clear(self):
        for ax in self.get_figure().axes:
            legend = ax.get_legend()
            if legend:
                legend.remove()

            for line in ax.get_lines():
                line.remove()
        self.redraw()

    def init(self):
        lines = []

        def init_ax(index, label):
            ax = self.plot.get_axis(index)
            line, = ax.plot([], [], label = label, marker = self.marker)
            return line

        for process in self.processes:
            label = "p {0}".format(process.id)
            for i in xrange(len(self.plot.plots)):
                lines.append(init_ax(i, label))

        for ax in self.plot.get_figure().axes:
            set_ax_color(ax)
            ax.legend(prop = {"size": 10})
        return lines

    def update_frame(self):
        lines = []

        def update_ax(index, xdata, ydata, line, label = None):
            ax = self.plot.get_axis(index)
            lines = ax.get_lines()
            l = lines[line - 1]
            xlen = len(l.get_xdata())
            ylen = len(l.get_ydata())
            if len(xdata) != xlen or len(ydata) != ylen:
                l.set_data(xdata, ydata)
                lines.append(l)
                ax.relim()
                ax.autoscale_view()

        line = 1
        c = color_pallete.new_color_cycler()
        bar_ax = self.plot.get_axis(1)
        del bar_ax.collections[:]

        for p in self.processes:
            mm = p.ctx.monitor_manager

            mem_monitor = mm.get_process_monitor(p.id, "MemoryMonitor")

            if mem_monitor:
                mem_entry = "memory_usage"
                mem_data = mem_monitor.collect([mem_entry])
                xdata = []
                ydata = []
                for val, size in mem_data[mem_entry]:
                    xdata.append(val)
                    ydata.append(size)
                update_ax(0, xdata, ydata, line, "time")

            edge_monitor = mm.get_process_monitor(p.id, "EdgeMonitor")
            if edge_monitor:
                edge_disc_time_entry = "edges_discovered_in_time"
                edge_calc_entry = "edge_calculated"
                edge_data = edge_monitor.collect([edge_calc_entry,
                                                  edge_disc_time_entry])
                xdata = []
                ydata = []
                for time, _, edge_time, _, _, _, _ in edge_data[edge_calc_entry]:
                    xdata.append(time)
                    ydata.append(edge_time)

                if len(xdata) and len(ydata) > 0:
                    ax = self.plot.get_axis(1)
                    ax.vlines(xdata, [0], ydata, color = next(c), label = "Calculating time")
                    ax.set_xlim([0, xdata[-1] + 2])
                    ax.set_ylim([0, max(ydata)])
                    self.plot.plots[1].legend_mapping(ax)

                xdata = []
                ydata = []
                for sim_time, storage_size in edge_data[edge_disc_time_entry]:
                    xdata.append(sim_time)
                    ydata.append(storage_size)
                update_ax(2, xdata, ydata, line, "time")

            line += 1
        return lines

