import gtk
import tab
import statistics
from canvas import Canvas
from nodeselector import NodeSelector
from sim.simulation import VisualSimulation
from dialogs.simulationdialog import SimulationDialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from gobject import gobject


class SimulationStatistics(statistics.Statistics):
    def __init__(self, simulation_tab):
        statistics.Statistics.__init__(self)
        self.sim_tab = simulation_tab
        self.create_properties()

    def create_properties(self):
        panel = self.sim_tab.properties_panel
        self.add_property("name", "Name:", "", panel)
        self.add_property("size", "Size:", "", panel)
        self.add_property("succesors", "Succesors:", "", panel)
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
        self.update_property("succesors", node.get_succesors_count())

    def update_statistics(self):
        self.update_property("pr_count", len(self.sim_tab.simulator.processes))
        self.update_property("alg", self.sim_tab.simulator.processes[0].get_name())
        self.update_property("nodes_count", len(self.sim_tab.graph.nodes))


class SimulationController():
    def __init__(self, sim_tab):
        self.simulator = sim_tab.simulator
        self.win = sim_tab.win
        self.sim_tab = sim_tab
        self.timer = None
        self.running = False
        self.step_count = 1
        self.end_simulation = False

    def request_sim_dialog(self):
        sim_dialog = SimulationDialog(self.win, self.simulator.get_available_processor_types())
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

    def _new_start(self):
        if not self.simulator.is_running():
            if not self.request_sim_dialog():
                return
            self.simulator.start()
            self.step_count = 1
            self._update_timers()
            self.sim_tab.sim_stats.update_statistics()
            self.end_simulation = False

    def _update_timers(self):
        self.sim_tab.sim_stats.update_property("step", self.step_count)
        self.sim_tab.sim_stats.update_property("sim_time", self.simulator.env.now)

    def run(self, interval = 1000):
        self._new_start()
        self.running = True
        self.timer = gobject.timeout_add(interval, self.step)

    def step(self):
        self._new_start()
        val = self.simulator.visible_step()
        if val:
            self.sim_tab.redraw()
            self.step_count += 1
            self._update_timers()
            self.sim_tab.redraw_plot()
            return True
        else:
            if not self.end_simulation:
                self.sim_tab.redraw()
                self.step_count += 1
                self._update_timers()
                self.sim_tab.redraw_plot()
                self.end_simulation = True
            return False

    def stop(self):
        if self.timer:
            if self.running:
                gobject.source_remove(self.timer)
                self.running = False
        self.simulator.stop()

    def restart(self):
        self.stop()
        self.simulator.graph.reset()
        self.sim_tab.redraw()


class SimulationTab(tab.CloseTab):
    def __init__(self, project, window):
        tab.CloseTab.__init__(self, project.get_project_name())
        self.project = project
        self.win = window
        self.figs = {}
        self.pack_start(self._create_content())
        self.sim_stats = SimulationStatistics(self)
        self.graph = self.project.get_visible_graph()
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
        hbox.pack_start(self._create_content_panel())
        hbox.pack_start(self._create_right_panel(), False, False)
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
            icons_path = "../resources/icons/"
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

        return toolbar

    def _create_properties_panel(self):
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("Node properties"), False, False)
        vbox.pack_start(hbox, False, False)
        return vbox

    def _create_content_panel(self):
        canvas = Canvas()
        canvas.set_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.KEY_PRESS_MASK | gtk.gdk.KEY_RELEASE_MASK)
        canvas.connect("configure_event", lambda w, e: self.redraw())
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        viewport = gtk.Viewport()
        sw.add(viewport)
        viewport.add(canvas)
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
            fig = plt.figure()
            fig_canvas = FigureCanvas(fig)
            fig_canvas.set_size_request(440,400)

            ax1 = plt.subplot2grid((4, 1), (0, 0))
            plt.tick_params(labelsize=8)
            ax2 = plt.subplot2grid((4, 1), (1, 0))
            plt.tick_params(labelsize=8)
            ax3 = plt.subplot2grid((4, 1), (2, 0))
            plt.tick_params(labelsize=8)
            ax4 = plt.subplot2grid((4, 1), (3, 0))
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
            self.fig = fig
            plots.pack_start(fig_canvas)
            
            return plots

        sw = gtk.ScrolledWindow()
        view = gtk.Viewport()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(view)
        view.add(create_plots())
        
        def on_configure(w,e):
            width = w.allocation.width
            height = w.allocation.height
            if width == e.width and height == e.height:
                return
            sw.set_size_request(int(e.width * 0.3), int(e.height * 0.3))

        self.conf_handler_id = self.win.connect("configure_event", on_configure)
        sw.set_size_request(int(self.win.allocation.width * 0.3),
                            int(self.win.allocation.height * 0.3))
        return sw

    def redraw_plot(self):
        axes = self.fig.axes

        def update_ax(index, xdata, ydata, line, label):
            ax = axes[index]
            lines = ax.get_lines()
            if len(lines) < line:
                ax.plot(xdata, ydata, label = label, marker = "o")
                return
            l = lines[line - 1]
            l.set_data(xdata, ydata)
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

        for ax in axes:
            ax.legend(prop = {"size":10})
        self.fig.canvas.draw()

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
            current_zoom += step
        else:
            if current_zoom - step >= 0:
                current_zoom -= step
            else:
                current_zoom = 0
        self.canvas.set_zoom(current_zoom)
        self.redraw()

    def on_mouse_click(self, w, e):
        """
        if e.button == 3:
            self.zoom(1)
        elif e.button == 2:
            self.zoom(-1)
        """
        selected_node = self.node_selector.get_node_at(int(e.x), int(e.y))

        if selected_node:
            if e.button == 1:
                self.update_node_info(selected_node)
            #if e.button == 3:
                #self.show_succesors(selected_node)
                #selected_node.succesors_count = 0
            self.redraw()

    def set_graph(self, graph):
        self.canvas.set_size_request(graph.width, graph.height)
        self.graph = graph
        self.graph.reset()
        self.node_selector = NodeSelector(self.graph)
        self.update_succesors_count(graph.get_root())
        self.redraw()

    def show_succesors(self, node):
        for edge in node.get_edges():
            destination_node = edge.get_destination()
            destination_node.set_visible(True)
            self.update_succesors_count(destination_node)

    def update_node_info(self, node):
        self.sim_stats.update_node_properties(node)

    def update_succesors_count(self, node):
        succesors_count = 0
        for e in node.get_edges():
            if not e.get_destination().is_visible():
                succesors_count += 1
        node.succesors_count = succesors_count

    def on_close(self, w, t):
        self.win.disconnect(self.conf_handler_id)
        self.controller.stop()
        tab.CloseTab.on_close(self, w, t)