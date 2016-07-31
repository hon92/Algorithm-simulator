import gtk
import paths
import ntpath
import plot
import exportmodule
import settings
import simulationcontroller as sc
from misc import timer
from gui import worker
from sim import simulation
from collections import deque
from gui.dialogs import dialog
from gui.exceptions import GraphException, VisibleGraphException
from sim import processfactory as pf
from canvas import Canvas
from nodeselector import NodeSelector
from gui import statistics



class Tab(gtk.VBox):
    def __init__(self, window, title):
        gtk.VBox.__init__(self)
        self.win = window
        self.show()
        self.title_text = title
        self.label = gtk.Label(self.title_text) 

    def set_title(self, title):
        self.label.set_text(title)

    def get_title(self):
        return self.title_text

    def get_tab_label(self):
        return self.label

    def close(self):
        self.win.remove_tab(self)

class CloseTab(Tab):
    def __init__(self, window, title):
        Tab.__init__(self, window, title)
        self.close_button = self._prepare_close_button()
        self.close_button.connect("clicked", lambda w: self.close())

    def _prepare_close_button(self):
        close_image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        btn = gtk.Button()
        btn.set_relief(gtk.RELIEF_NONE)
        btn.set_focus_on_click(False)
        btn.add(close_image)
        style = gtk.RcStyle()
        style.xthickness = 0
        style.ythickness = 0
        btn.modify_style(style)
        return btn

    def get_tab_label(self):
        hbox = gtk.HBox()
        hbox.pack_start(self.label)
        hbox.pack_start(self.close_button, False, False)
        hbox.show_all()
        return hbox

class WelcomeTab(CloseTab):
    def __init__(self, window, title):
        CloseTab.__init__(self, window, title)
        self.pack_start(gtk.Label("Welcome in simulator"))

class ProjectTab(Tab):
    def __init__(self, window, project):
        Tab.__init__(self, window, "Project")
        self.project = project
        self.win.set_title(project.get_name())
        self._create_content()

    def _create_content(self):
        glade_file = paths.GLADE_DIALOG_DIRECTORY + "project_tab.glade"
        builder = gtk.Builder()
        builder.add_from_file(glade_file)

        self.box = builder.get_object("vbox")
        self.treeview = builder.get_object("treeview")
        self.treeview.set_property("hover-selection", True)
        self.liststore = builder.get_object("liststore")
        self.toggle_render = builder.get_object("cellrenderertoggle1")
        self.add_button = builder.get_object("add_button")
        self.remove_button = builder.get_object("remove_button")
        self.sim_button = builder.get_object("run_sim_button")
        self.viz_button = builder.get_object("run_viz_button")
        self.combobox = builder.get_object("combobox")
        self.process_num_button = builder.get_object("process_num_button")
        self.sim_num_button = builder.get_object("sim_num_button")
        self.pack_start(self.box)
        self._connect_signals()

    def _connect_signals(self):
        self.toggle_render.connect("toggled", self.on_selected_toggled)
        self.add_button.connect("clicked", lambda w: self.load_graph_file())
        self.remove_button.connect("clicked", lambda w: self.remove_graph_file())
        self.sim_button.connect("clicked", lambda w: self.run_simulations())
        self.viz_button.connect("clicked", lambda w: self.run_vizual_simulations())

    def load(self):
        algorithms = pf.get_process_names()
        for alg in algorithms:
            self.combobox.append_text(alg)
        self.combobox.set_active(0)

        for filename in self.project.get_files():
            self.add_graph(filename)

    def add_graph(self, filename):
        graph = self.project.graph_manager.get_origin_graph(filename)
        nodes = graph.get_nodes_count()
        edges = graph.get_edges_count()
        self.liststore.append([False, filename, nodes, edges])
        info = "Graph '{0}' added to project"
        self.win.console.writeln(info.format(filename))

    def on_selected_toggled(self, w, iter):
        self.liststore[iter][0] = not self.liststore[iter][0]

    def load_graph_file(self):
        graph_file = dialog.Dialog.get_factory("xml").open("Open graph file")

        if graph_file:
            try:
                self.project.load_graph_file(graph_file)
                self.add_graph(graph_file)
            except Exception as ex:
                self.win.console.writeln(ex.message, "err")

    def remove_graph_file(self):
        for row in self.liststore:
            if row[0]:
                msg = "'{0}' was removed from project"
                self.win.console.writeln(msg.format(row[1]))
                self.project.remove_graph_file(row[1])
                self.liststore.remove(row.iter)

    def run_simulations(self,
                        files = None,
                        sim_count = None,
                        process_type = None,
                        process_count = None):

        if not files:
            files = []
        if not process_count:
            process_count = self.process_num_button.get_value_as_int()
        if not process_type:
            process_type = self.combobox.get_active_text()
        if not sim_count:
            sim_count = self.sim_num_button.get_value_as_int()

        try:
            for row in self.liststore:
                if row[0]:
                    filename = row[1]
                    files.append(filename)

            sim_properties = {
                "sim_count": sim_count,
                "process_type": process_type,
                "process_count": process_count,
                "files": files
            }
            if len(files):
                self.win.create_tab(SimulationProgressTab(self.win,
                                                          "Simulation",
                                                          self.project,
                                                          sim_properties))
        except GraphException as ex:
            self.win.console.writeln(ex.message, "err")

    def run_vizual_simulations(self):
        for row in self.liststore:
            if row[0]:
                if int(row[2]) > settings.MAX_VISIBLE_GRAPH_NODES:
                    err_text = "Graph {0} was skipped because is too big" + \
                               " (max graph nodes count is {1})"
                    err_text = err_text.format(row[1], str(settings.MAX_VISIBLE_GRAPH_NODES))
                    self.win.console.writeln(err_text, "err")
                    continue
                try:
                    title = "Viz. sim - " + ntpath.basename(row[1])
                    self.win.create_tab(VizualSimulationTab(self.win,
                                                            title,
                                                            self.project,
                                                            row[1]))
                except VisibleGraphException as ex:
                    self.win.console.writeln(ex.message, "err")

class SimulatorTab(CloseTab):
    def __init__(self, window, title, filename, simulator):
        CloseTab.__init__(self, window, title)
        self.simulator = simulator
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_LEFT)
        sw.add_with_viewport(self.notebook)
        self.statistics = self._create_statistics(filename)
        self.pack_start(sw)
        self.plots = []

    def create_plots(self):
        def add_plot_page(widget, title):
            self.notebook.append_page(widget, gtk.Label(title))
            self.plots.append(widget.plot)

        self.notebook.append_page(self.statistics, gtk.Label("Results"))
        memory_usage_plot = plot.MemoryUsagePlot(self.simulator)
        calculated_plot = plot.CalculatedBarPlot(self.simulator)

        add_plot_page(memory_usage_plot.get_widget_with_navbar(self.win),
                      memory_usage_plot.get_title())
        add_plot_page(calculated_plot.get_widget(), calculated_plot.get_title())

        for process in self.simulator.processes:
            process_plot = plot.ProcessPlot(process)
            add_plot_page(process_plot.get_widget_with_navbar(self.win), process_plot.get_title())

        self.notebook.connect("switch-page", self.on_page_switch)
        self.show_all()

    def on_page_switch(self, notebook, page, num):
        if num > 0:
            tab = notebook.get_nth_page(num)
            if tab:
                selected_plot = tab.plot 
                selected_plot.draw()

    def _create_statistics(self, filename):
        vbox = gtk.VBox()
        builder = gtk.Builder()
        builder.add_from_file(paths.GLADE_DIALOG_DIRECTORY + "tree_statistics.glade")
        stat_widget = builder.get_object("vbox")
        info_store = builder.get_object("infostore")
        sim_stats = statistics.SimulationStatistics(info_store)
        sim_stats.init()
        sim_stats.update_graph(filename, self.simulator.graph)
        sim_stats.new_simulation(self.simulator)
        sim_stats.update_prop("sim_time", self.simulator.env.now)
        sim_stats.update_processes(self.simulator.processes)
        vbox.pack_start(stat_widget)
        return vbox

    def close(self):
        for p in self.plots:
            p.dispose()
        CloseTab.close(self)

class SimulationProgressTab(CloseTab):
    PROGRESS_BAR_REFRESH_TIME = 100
    RUNNING = "In progress"
    CANCELED = "Canceled"
    WAITING = "Pending"
    COMPLETED = "Completed"

    def __init__(self, window, title, project, sim_properties):
        CloseTab.__init__(self, window, title)
        self.project = project
        self.sim_props = sim_properties
        self.liststore = gtk.ListStore(str, int, str, float, str) # process type, progress, status, time, filename
        self.sim_q = deque()
        self.opened_tabs = []
        self.current_iter = -1
        self.sim = None
        self.completed_simulations = {} # key -> index_row, val -> simulation
        self.used_graphs = {}
        self.timer = timer.Timer(self.PROGRESS_BAR_REFRESH_TIME, self.on_timeout)
        self._create_content()
        self._prepare_data()
        self.worker = worker.SimWorker()
        self.worker.setDaemon(True)
        self.worker.add_callback(lambda s: self.on_sim_complete(s, self.current_iter))
        self.worker.add_error_callback(self.on_sim_error)
        self.worker.start()
        self.start_next_sim()

    def _prepare_data(self):
        sim_count = self.sim_props["sim_count"]
        process_count = self.sim_props["process_count"]
        process_type = self.sim_props["process_type"]
        files = self.sim_props["files"]

        for filename in files:
            self.used_graphs[filename] = self.project.graph_manager.get_graph(filename)

        for _ in xrange(sim_count):
            for filename in files:
                graph = self.used_graphs[filename]
                simulator = simulation.Simulation(graph)
                simulator.register_n_processes(process_type, process_count)
                for process in simulator.processes:
                    process.connect("log", self._log_message)
                process_info = "{0} - {1}({2})".format(ntpath.basename(filename),
                                                      process_type,
                                                      process_count)
                self.liststore.append([process_info, 0, self.WAITING, 0.0, filename])
                self.sim_q.append(simulator)

    def _log_message(self, msg, tag):
        self.win.console.writeln(msg, tag)

    def _create_content(self):
        def create_button(icon, tooltip, callback):
            button = gtk.Button()
            image = gtk.Image()
            image.set_from_file(paths.ICONS_PATH + icon)
            button.add(image)
            button.set_tooltip_text(tooltip)
            button.connect("clicked", lambda w: callback())
            button.show_all()
            return button

        export_button = create_button("CSV-24.png",
                                      "Export data to CSV",
                                      self.on_export)

        cancel_button = create_button("Close Window-24.png",
                                      "Cancel simulation",
                                      self.on_cancel)

        show_button = create_button("Show Property-24.png",
                                      "Show results",
                                      self.on_show_results)

        self.treeview = self._create_tree_view()
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add_with_viewport(self.treeview)
        self.pack_start(sw)
        hbox = gtk.HBox()
        hbox.pack_start(show_button)
        hbox.pack_start(export_button)
        hbox.pack_start(cancel_button)
        self.pack_start(hbox, False)
        self.show_all()

    def _create_tree_view(self):
        treeview = gtk.TreeView(model = self.liststore)

        renderer_text = gtk.CellRendererText()
        renderer_text.set_property("xalign", 0.5)
        col1 = gtk.TreeViewColumn("Test info")
        col1.set_property("alignment", 0.5)
        col1.set_min_width(150)
        col1.pack_start(renderer_text)
        col1.add_attribute(renderer_text, "text", 0)

        renderer_progress = gtk.CellRendererProgress()
        renderer_progress.set_property("xalign", 0.5)
        col2 = gtk.TreeViewColumn("Simulation progress")
        col2.set_property("alignment", 0.5)
        col2.set_min_width(200)
        col2.pack_start(renderer_progress)
        col2.add_attribute(renderer_progress, "value", 1)

        renderer_text = gtk.CellRendererText()
        renderer_text.set_property("xalign", 0.5)
        col3 = gtk.TreeViewColumn("Status")
        col3.set_property("alignment", 0.5)
        col3.set_min_width(50)
        col3.pack_start(renderer_text)
        col3.add_attribute(renderer_text, "text", 2)

        renderer_text = gtk.CellRendererText()
        renderer_text.set_property("xalign", 0.5)
        col4 = gtk.TreeViewColumn("Test info")
        col4.set_property("alignment", 0.5)
        col4.set_min_width(50)
        col4.pack_start(renderer_text)
        col4.add_attribute(renderer_text, "text", 3)

        treeview.append_column(col1)
        treeview.append_column(col2)
        treeview.append_column(col3)
        treeview.append_column(col4)
        return treeview

    def start_next_sim(self):
        self.set_title("Simulation ({0}/{1})".format(self.current_iter + 1,
                                                     self.sim_props["sim_count"] * 
                                                     len(self.sim_props["files"])))
        if len(self.sim_q):
            self.sim = self.sim_q.pop()
            self.current_iter += 1
            self.liststore[self.current_iter][2] = self.RUNNING
            self.timer.restart()
            self.worker.put(self.sim)

    def on_timeout(self):
        if not self.sim:
            return False
        if self.sim and hasattr(self.sim, "sim_status"):
            return False
        nodes_count = self.sim.graph.get_nodes_count()
        curr_nodes = self.sim.graph.get_discovered_nodes_count()
        new_val = curr_nodes / float(nodes_count)
        self.liststore[self.current_iter][1] = int(new_val * 100)
        if new_val >= 1.0:
            return False
        return True

    def on_sim_complete(self, sim, iter):
        status = sim.sim_status
        if not status:
            self.liststore[iter][2] = self.COMPLETED
            self.liststore[iter][3] = sim.env.now
            self.liststore[iter][1] = 100
            self.completed_simulations[iter] = sim
        else:
            self.liststore[iter][2] = self.CANCELED
            self.liststore[iter][3] = -1
            self.liststore[iter][1] = 0
        self.start_next_sim()

    def on_sim_error(self, sim, msg):
        iter = self.current_iter
        self.liststore[iter][2] = self.CANCELED
        self.liststore[iter][3] = -1
        self.liststore[iter][1] = 0
        self._log_message(self.liststore[iter][0] + ": " + msg, "err")
        self.start_next_sim()

    def on_cancel(self):
        index = self.get_selected_row_index()
        if index > -1:
            if self.liststore[index][2] == self.RUNNING:
                if self.sim:
                    self.sim.stop()

    def on_export(self):
        index = self.get_selected_row_index()
        if index > -1:
            if self.liststore[index][2] == self.COMPLETED:
                if index not in self.completed_simulations:
                    return
                sim = self.completed_simulations[index]
                new_file = dialog.Dialog.get_factory("csv").save_as("Save simulation detail as")
                if new_file:
                    ex = exportmodule.CSVExportDataModule(sim)
                    try:
                        ex.print_to_file(new_file)
                        msg = "Data was exported to '{0}'"
                        self.win.console.writeln(msg.format(new_file))
                    except IOError as ex:
                        msg = "Export data to file '{0}' failed"
                        self.win.console.writeln(msg.format(new_file), "err")

    def on_show_results(self):
        index = self.get_selected_row_index()
        if index > -1:
            if self.liststore[index][2] == self.COMPLETED:
                if index in self.completed_simulations:
                    sim = self.completed_simulations[index]
                    title = self.liststore[index][0]
                    simulator_tab = SimulatorTab(self.win,
                                                 title + "- Detail",
                                                 self.liststore[index][4],
                                                 sim)
                    self.win.create_tab(simulator_tab)
                    self.opened_tabs.append(simulator_tab)
                    simulator_tab.create_plots()

    def get_selected_row_index(self):
        tree_selection = self.treeview.get_selection()
        if tree_selection:
            model, rows = tree_selection.get_selected_rows()
            if rows:
                return rows[0][0]
        return -1

    def get_selected_row(self):
        index = self.get_selected_row_index()
        if index == -1:
            return None
        return self.liststore[index]

    def close(self):
        self.timer.stop()
        self.sim_q.clear()
        if self.sim:
            self.sim.stop()
        del self.sim
        self.worker.quit()
        del self.worker
        for tab in self.opened_tabs:
            tab.close()
        for f in self.used_graphs:
            self.project.graph_manager.return_graph(f, self.used_graphs[f])
        CloseTab.close(self)

class VizualSimulationTab(CloseTab):
    def __init__(self, window, title, project, filename):
        CloseTab.__init__(self, window, title)
        self.project = project
        self.filename = filename
        self.selected_node = None
        self.graph = self.project.graph_manager.get_visible_graph(filename)
        self.graph.reset()

        builder = gtk.Builder()
        builder.add_from_file(paths.GLADE_DIALOG_DIRECTORY + "visual_sim_tab.glade")
        vbox = builder.get_object("vbox")
        toolbar = builder.get_object("toolbar")
        self.statusbar = builder.get_object("statusbar")
        self.status_ctx = self.statusbar.get_context_id("Simulation state")

        canvas = Canvas()
        canvas.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        canvas.connect("configure_event", lambda w, e: self.redraw())
        canvas.connect("button_press_event", lambda w, e: self.on_mouse_click(e))
        canvas.set_size_request(self.graph.width, self.graph.height)
        canvas_container = builder.get_object("canvascontainer")
        canvas_container.pack_start(canvas)
        self.canvas = canvas

        self.anim_plot = plot.VizualSimPlotAnim()

        marker_button = builder.get_object("markerbutton")
        navbar_button = builder.get_object("navbarbutton")
        time_button = builder.get_object("timebutton")
        step_button = builder.get_object("stepbutton")

        marker_button.set_active(self.anim_plot.has_marker())
        navbar_button.set_active(self.anim_plot.has_navbar())
        if self.anim_plot.get_unit() == "time":
            time_button.set_active(True)
        else:
            step_button.set_active(True)

        marker_button.connect("toggled", self.on_marker_button_toggle)
        navbar_button.connect("toggled", self.on_navbar_button_toggle)
        time_button.connect("toggled", self.on_unit_change, "time")
        step_button.connect("toggled", self.on_unit_change, "step")

        plotvbox = builder.get_object("plotvbox")
        plotvbox.pack_start(self.anim_plot.create_widget(window))
        self.pack_start(vbox)
        self.simulator = simulation.VisualSimulation(self.graph)
        self.node_selector = NodeSelector(self.graph)
        self.controller = sc.SimulationController(self, toolbar)

        properties_store = builder.get_object("propertystore")
        self.state_stats = statistics.StateStatistics(properties_store)
        self.state_stats.init()

        info_store = builder.get_object("infostore")
        self.sim_stats = statistics.SimulationStatistics(info_store)
        self.sim_stats.init()
        self.sim_stats.update_graph(self.filename, self.graph)
        self.show_all()


#     def _create_right_panel(self):
#         self.anim_plot = VizualSimPlotAnim(self.init_plots,
#                                            self.animate,
#                                            self.frames_gen)
#         sw = gtk.ScrolledWindow()
#         sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
#         sw.add_with_viewport(self.anim_plot.get_widget())
# 
#         def on_configure(w,e):
#             width = w.allocation.width
#             height = w.allocation.height
#             if width == e.width and height == e.height:
#                 return
#             sw.set_size_request(int(e.width * 0.3), int(e.height * 0.3))
#             self.hpaned.set_position(e.width - sw.allocation.width)
# 
#         self.win.connect("configure_event", on_configure)
#         sw.set_size_request(int(self.win.allocation.width * 0.3),
#                             int(self.win.allocation.height * 0.3))
#         self.hpaned.set_position(self.win.allocation.width - sw.allocation.width)
#         return sw

    def on_marker_button_toggle(self, button):
        marker = ""
        if button.get_active():
            marker = "o"

        self.anim_plot.set_marker(marker)

    def on_navbar_button_toggle(self, button):
        self.anim_plot.show_navbar(button.get_active())

    def on_unit_change(self, button, data):
        if button.get_active():
            self.anim_plot.set_unit(data)

    def redraw(self):
        self.canvas.set_color(240,240,240)
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

    def switch_selected_node(self, node):
        if self.selected_node:
            self.selected_node.is_selected = False

        if node:
            self.selected_node = node
            self.selected_node.is_selected = True
            self.update_node_info(node)
        else:
            self.state_stats.reset()
        self.redraw()

    def on_mouse_click(self, e):
        if e.button != 1:
            return

        zoom = self.canvas.get_zoom()
        selected_node = self.node_selector.get_node_at(int(e.x), int(e.y), zoom)
        self.switch_selected_node(selected_node)

    def update_node_info(self, node):
        self.state_stats.update(node, self.simulator)

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
        CloseTab.close(self)
