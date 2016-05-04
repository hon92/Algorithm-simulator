import gtk
import paths
import settings
import tab
import statistics
import matplotlib.pyplot as plt
from canvas import Canvas
from misc import utils
from nodeselector import NodeSelector
from sim.simulation import VisualSimulation
from dialogs.simulationdialog import SimulationDialog
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib import animation
from misc import timer

class SimulationStatistics(statistics.Statistics):
    def __init__(self, simulation_tab):
        statistics.Statistics.__init__(self)
        self.sim_tab = simulation_tab
        self.create_properties()

    def create_properties(self):
        panel = self.sim_tab.properties_panel
        self.add_property("name", "Name:", "", panel)
        self.add_property("size", "Size:", "", panel)
        self.add_property("discovered_by", "Discovered by process:", "", panel)

        panel = self.sim_tab.statistics_panel
        self.add_property("sim_time", "Simulation time:", "", panel)
        self.add_property("pr_count", "Process count:", "", panel)
        self.add_property("alg", "Algorithm:", "", panel)
        self.add_property("step", "Sim steps:", "", panel)
        self.add_property("nodes_count", "Nodes:", "", panel)

    def update_node_properties(self, node):
        self.update_property("name", node.get_name())
        self.update_property("size", node.get_size())
        self.update_property("discovered_by", node.get_discoverer())

    def update_statistics(self):
        self.update_property("pr_count", len(self.sim_tab.simulator.processes))
        self.update_property("alg", self.sim_tab.simulator.processes[0].get_name())
        self.update_property("nodes_count", len(self.sim_tab.graph.nodes))

class SimulationController():

    def __init__(self, sim_tab):
        self.simulator = sim_tab.simulator
        self.sim_tab = sim_tab
        self.step_count = 0
        self.timer = timer.Timer(settings.VIZ_SIMULATION_TIMER, self.step)
        
    def request_sim_dialog(self):
        sim_dialog = SimulationDialog(self.sim_tab.win,
                                      self.simulator.get_available_processor_types())
        result = sim_dialog.run()
        if result != gtk.RESPONSE_OK:
            sim_dialog.destroy()
            return False
        process_count = sim_dialog.get_process_count()
        process_type = sim_dialog.get_process_type()
        sim_dialog.destroy()
        self.simulator.stop()
        self.simulator.register_n_processes(process_type, process_count)
        return True

    def set_graph_colors(self):
        self.sim_tab.fig.gca().set_prop_cycle(None)
        color_cycler = self.sim_tab.fig.gca()._get_lines.prop_cycler
        colors = []
        for i in xrange(len(self.simulator.processes)):
            color_dict = next(color_cycler)
            hex_color = color_dict["color"]
            colors.append(utils.hex_to_rgb(hex_color))
        self.sim_tab.graph.set_colors(colors)

    def _update_timers(self):
        self.step_count += 1 
        self.sim_tab.sim_stats.update_property("step", self.step_count)
        self.sim_tab.sim_stats.update_property("sim_time", self.simulator.env.now)

    def run(self):
        if not self.simulator.is_running():
            if not self.request_sim_dialog():
                return
            self.step_count = 0
            self.set_graph_colors()
            self.simulator.start()
            self.sim_tab.clear_plots()
            self._update_timers()
            self.sim_tab.sim_stats.update_statistics()
            self.sim_tab.run_animated_plots()
            self.timer.start()

    def step(self):
        if self.simulator.is_running():
            self._step()
            self.sim_tab.redraw()
            self._update_timers()
            return True
        else:
            return False

    def _step(self):
        val = self.simulator.visible_step()
        if not val:
            self.simulator.running = False

    def stop(self):
        self.timer.stop()
        self.simulator.stop()

    def restart(self):
        self.stop()
        self.simulator.graph.reset()
        self.sim_tab.clear_plots()
        self.sim_tab.redraw()

class VizualSimulationTab(tab.CloseTab):
    def __init__(self, title, visible_graph, window):
        tab.CloseTab.__init__(self, title)
        self.win = window
        self.pack_start(self._create_content())
        self.sim_stats = SimulationStatistics(self)
        self.graph = visible_graph
        self.simulator = VisualSimulation(self.graph)
        self.controller = SimulationController(self)
        self.canvas.connect("button_press_event", self.on_mouse_click)
        self.node_selector = None
        self.show_all()

    def _create_content(self):
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        vbox.pack_start(self._create_toolbar(), False, False)
        self.properties_panel = self._create_properties_panel()
        hbox.pack_start(self.properties_panel, False, False)
        self.hpaned = gtk.HPaned()
        self.hpaned.pack1(self._create_content_panel(), True, False)
        self.hpaned.pack2(self._create_right_panel(), True, False)
        hbox.pack_start(self.hpaned)
        vbox.pack_start(hbox)
        self.statistics_panel = self._create_statistics_panel()
        vbox.pack_start(self.statistics_panel, False, False)
        return vbox

    def _create_toolbar(self):
        toolbar = gtk.Toolbar()
        toolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        toolbar.set_style(gtk.TOOLBAR_BOTH)
        toolbar.set_border_width(5)
        self.toolbar = toolbar

        def get_image(icon_name):
            image = gtk.Image()
            icons_path = paths.ICONS_PATH
            image.set_from_file(icons_path + icon_name)
            image.show()
            return image

        toolbar.append_item(
            "Run",           # button label
            "Run simulation", # this button's tooltip
            "Private",         # tooltip private info
            get_image("Play-24.png"),             # icon widget
            lambda e: self.controller.run()) # a signal

        toolbar.append_item(
            "Run one step",           # button label
            "Run one step in simulation", # this button's tooltip
            "Private",         # tooltip private info
            get_image("Play-24.png"),             # icon widget
            lambda e: self.controller.step()) # a signal

        toolbar.append_space() # space after item

        toolbar.append_item(
            "Stop",           # button label
            "Stop simulation", # this button's tooltip
            "Private",         # tooltip private info
            get_image("Stop-24.png"),             # icon widget
            lambda e: self.controller.stop()) # a signal

        toolbar.append_item(
            "Reset",           # button label
            "Reset simulation", # this button's tooltip
            "Private",         # tooltip private info
            get_image("Restart-24.png"),             # icon widget
            lambda e: self.controller.restart()) # a signal

        toolbar.append_item(
            "Zoom in",           # button label
            "Zoom in", # this button's tooltip
            "Private",         # tooltip private info
            get_image("Zoom In-24.png"),             # icon widget
            lambda e: self.zoom(1)) # a signal

        toolbar.append_item(
            "Zoom out",           # button label
            "Zoom out", # this button's tooltip
            "Private",         # tooltip private info
            get_image("Zoom Out-24.png"),             # icon widget
            lambda e: self.zoom(-1)) # a signal

        return toolbar

    def _create_properties_panel(self):
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("Node properties"), False, False)
        vbox.pack_start(hbox, False, False)
        return vbox

    def _create_content_panel(self):
        canvas = Canvas()
        canvas.set_events(gtk.gdk.BUTTON_PRESS_MASK |
                          gtk.gdk.KEY_PRESS_MASK |
                          gtk.gdk.KEY_RELEASE_MASK)
        canvas.connect("configure_event", lambda w, e: self.redraw())
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add_with_viewport(canvas)
        self.canvas = canvas
        return sw

    def _create_statistics_panel(self):
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("Visual simulation info"))
        vbox.pack_start(hbox, False, False)
        return vbox

    def _create_right_panel(self):

        def create_plots():
            plots = gtk.VBox()
            self.fig = plt.figure()
            ax1 = self.fig.add_subplot(411)
            plt.tick_params(labelsize=8)
            ax2 = self.fig.add_subplot(412)
            plt.tick_params(labelsize=8)
            ax3 = self.fig.add_subplot(413)
            plt.tick_params(labelsize=8)
            ax4 = self.fig.add_subplot(414)
            plt.tick_params(labelsize=8)
            ax1.set_title("Memory uses", fontdict = {"fontsize":10})
            ax1.set_xlabel("time", fontdict = {"fontsize":10})
            ax1.set_ylabel("size", fontdict = {"fontsize":10})
            ax2.set_title("Calculated", fontdict = {"fontsize":10})
            ax2.set_xlabel("time", fontdict = {"fontsize":10})
            ax2.set_ylabel("count", fontdict = {"fontsize":10})
            ax3.set_title("Edges discovered", fontdict = {"fontsize":10})
            ax3.set_xlabel("time", fontdict = {"fontsize":10})
            ax3.set_ylabel("count", fontdict = {"fontsize":10})
            ax4.set_title("Edges completed", fontdict = {"fontsize":10})
            ax4.set_xlabel("time", fontdict = {"fontsize":10})
            ax4.set_ylabel("count", fontdict = {"fontsize":10})
            plt.tight_layout(w_pad = -2.3)
            fig_canvas = FigureCanvas(self.fig)
            plots.pack_start(fig_canvas)
            return plots

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add_with_viewport(create_plots())

        def on_configure(w,e):
            width = w.allocation.width
            height = w.allocation.height
            if width == e.width and height == e.height:
                return
            sw.set_size_request(int(e.width * 0.3), int(e.height * 0.3))
            self.hpaned.set_position(e.width - sw.allocation.width)

        self.conf_handler_id = self.win.connect("configure_event", on_configure)
        sw.set_size_request(int(self.win.allocation.width * 0.3),
                            int(self.win.allocation.height * 0.3))
        self.hpaned.set_position(self.win.allocation.width - sw.allocation.width)
        return sw

    def run_animated_plots(self):
        def gen():
            i = 0
            last_update = False
            while True:
                if last_update:
                    break
                if not self.controller.simulator.is_running():
                    last_update = True
                    yield i + 1
                else:
                    i += 1
                    yield i

        self.anim = animation.FuncAnimation(self.fig,
                                            self.animate,
                                            init_func = self.init_plots,
                                            interval = 1000,
                                            frames = gen,
                                            repeat = False)
        self.fig.canvas.draw()

    def init_plots(self):
        axes = self.fig.axes
        lines = []
        def init_ax(index, label):
            ax = axes[index]
            line, = ax.plot([], [], label = label, marker = "o")
            return line

        for process in self.simulator.processes:
            label = "p {0}".format(process.id)
            lines.append(init_ax(0, label))
            lines.append(init_ax(1, label))
            lines.append(init_ax(2, label))
            lines.append(init_ax(3, label))

        for ax in self.fig.axes:
            ax.set_prop_cycle(None)
            ax.legend(prop = {"size":10})
        plt.tight_layout(w_pad = -2.3)
        return lines

    def animate(self, i):
        axes = self.fig.axes
        lines = []

        def update_ax(index, xdata, ydata, line, label):
            ax = axes[index]
            lines = ax.get_lines()
            l = lines[line - 1]
            l.set_data(xdata, ydata)
            lines.append(l)
            ax.relim()
            ax.autoscale_view()

        line = 1
        for process in self.simulator.processes:
            mon = process.monitor

            xdata, ydata = mon.get_data("memory_usage")
            update_ax(0, xdata, ydata, line, "p {0}".format(process.id))
            
            xdata, ydata = mon.get_data("edges_calculated")
            update_ax(1, xdata, ydata, line, "p {0}".format(process.id))

            xdata, ydata = mon.get_data("edge_discovered")
            update_ax(2, xdata, ydata, line, "pd {0}".format(process.id))

            xdata, ydata = mon.get_data("edge_completed")
            update_ax(3, xdata, ydata, line, "pc {0}".format(process.id))
            line += 1
        return lines

    def start(self):
        self.set_graph(self.graph)

    def redraw(self):
        self.canvas.set_color(240, 230, 220)
        self.canvas.draw_rectangle(0, 0, self.canvas.allocation.width, self.canvas.allocation.height, True)
        if self.graph:
            self.graph.draw(self.canvas)
            self.canvas.repaint()

    def zoom(self, dir = 1, step = 0.2):
        current_zoom = self.canvas.get_zoom()
        if dir == 1:
            if current_zoom + step <= 1:
                current_zoom += step
        else:
            if round(current_zoom, 1) - step > 0.0:
                current_zoom -= step

        self.canvas.set_zoom(current_zoom)
        self.redraw()

    def on_mouse_click(self, w, e):
        selected_node = self.node_selector.get_node_at(int(e.x), int(e.y))

        if selected_node:
            if e.button == 1:
                self.update_node_info(selected_node)
            self.redraw()

    def set_graph(self, graph):
        self.canvas.set_size_request(graph.width, graph.height)
        self.graph = graph
        self.graph.reset()
        self.node_selector = NodeSelector(self.graph)
        self.redraw()

    def show_succesors(self, node):
        for edge in node.get_edges():
            destination_node = edge.get_destination()
            destination_node.set_visible(True)
            self.update_succesors_count(destination_node)

    def update_node_info(self, node):
        self.sim_stats.update_node_properties(node)

    def on_close(self, w, t):
        #self.win.disconnect(self.conf_handler_id)
        self.controller.stop()
        self.fig.clf()
        plt.close(self.fig)
        tab.CloseTab.on_close(self, w, t)

    def clear_plots(self):
        for ax in self.fig.axes:
            for line in ax.get_lines():
                line.remove()

        self.fig.canvas.draw()
