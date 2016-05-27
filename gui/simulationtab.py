import gtk
import paths
import settings
import tab
from canvas import Canvas
from misc import utils
from nodeselector import NodeSelector
from statistics import SimulationStatistics
from sim.simulation import VisualSimulation
from dialogs.simulationdialog import SimulationDialog
from plot import VizualSimPlotAnim, set_ax_color
from misc import timer, colors as color_palette

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
        for process in self.simulator.processes:
            process.connect("log", self._log_message)
        return True

    def _log_message(self, msg, tag):
        self.sim_tab.win.console.writeln(msg, tag)

    def set_graph_colors(self):
        cc = color_palette.new_color_cycler()
        colors = []
        for _ in xrange(len(self.simulator.processes)):
            colors.append(utils.hex_to_rgb(next(cc)))
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

    def pause(self):
        if self.timer.is_running():
            self.timer.stop()
        else:
            if self.simulator.is_running():
                self.timer = timer.Timer(settings.VIZ_SIMULATION_TIMER, self.step)
                self.timer.start()

    def restart(self):
        self.stop()
        self.simulator.graph.reset()
        self.sim_tab.clear_plots()
        self.sim_tab.redraw()

class VizualSimulationTab(tab.CloseTab):
    def __init__(self, window, title, project, filename):
        tab.CloseTab.__init__(self, window, title)
        self.project = project
        self.filename = filename
        self.graph = self.project.graph_manager.get_visible_graph(filename)
        self.graph.reset()
        self.pack_start(self._create_content())
        self.sim_stats = SimulationStatistics(self)
        self.simulator = VisualSimulation(self.graph)
        self.controller = SimulationController(self)
        self.node_selector = NodeSelector(self.graph)
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
            "Pause",           # button label
            "Pause simulation", # this button's tooltip
            "Private",         # tooltip private info
            get_image("Pause-24.png"),             # icon widget
            lambda e: self.controller.pause()) # a signal

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
        canvas.connect("button_press_event", lambda w, e: self.on_mouse_click(e))
        canvas.set_size_request(self.graph.width, self.graph.height)
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
        self.anim_plot = VizualSimPlotAnim(self.init_plots,
                                           self.animate,
                                           self.frames_gen)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add_with_viewport(self.anim_plot.get_widget())

        def on_configure(w,e):
            width = w.allocation.width
            height = w.allocation.height
            if width == e.width and height == e.height:
                return
            sw.set_size_request(int(e.width * 0.3), int(e.height * 0.3))
            self.hpaned.set_position(e.width - sw.allocation.width)

        self.win.connect("configure_event", on_configure)
        sw.set_size_request(int(self.win.allocation.width * 0.3),
                            int(self.win.allocation.height * 0.3))
        self.hpaned.set_position(self.win.allocation.width - sw.allocation.width)
        return sw

    def frames_gen(self):
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

    def run_animated_plots(self):
        self.anim_plot.start()

    def init_plots(self):
        fig = self.anim_plot.get_figure()
        axes = fig.axes
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

        for ax in fig.axes:
            set_ax_color(ax)
            ax.legend(prop = {"size": 10})
        return lines

    def animate(self, i):
        axes = self.anim_plot.get_figure().axes
        lines = []

        def update_ax(index, xdata, ydata, line, label):
            ax = axes[index]
            lines = ax.get_lines()
            l = lines[line - 1]
            l.set_data(xdata, ydata)
            lines.append(l)
            ax.set_ymargin(0.2)
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

    def redraw(self):
        self.canvas.set_color(240, 230, 220)
        self.canvas.draw_rectangle(0, 0, self.canvas.allocation.width,
                                   self.canvas.allocation.height, True)
        self.graph.draw(self.canvas)
        self.canvas.repaint()

    def zoom(self, direction = 1, step = 0.2):
        current_zoom = self.canvas.get_zoom()
        if direction == 1:
            if current_zoom + step <= 1:
                current_zoom += step
        else:
            if round(current_zoom, 1) - step > 0.0:
                current_zoom -= step

        self.canvas.set_zoom(current_zoom)
        self.redraw()

    def on_mouse_click(self, e):
        selected_node = self.node_selector.get_node_at(int(e.x), int(e.y))

        if selected_node:
            if e.button == 1:
                self.update_node_info(selected_node)
            self.redraw()

    def update_node_info(self, node):
        self.sim_stats.update_node_properties(node)

    def clear_plots(self):
        for ax in self.anim_plot.get_figure().axes:
            for line in ax.get_lines():
                line.remove()
        self.anim_plot.get_figure().canvas.draw()

    def close(self):
        self.controller.stop()
        self.anim_plot.dispose()
        self.project.graph_manager.return_graph(self.filename,
                                                self.graph, True)
        self.canvas.dispose()
        tab.CloseTab.close(self)
