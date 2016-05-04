import gtk
import paths
import ntpath
import threading
import plot
import exportmodule
import settings
from statistics import PlotStatistics
from misc import timer
from sim import simulation
from dialogs import csvdialog as csvd, messagedialog as msgd, xmldialog as xmld

class Tab(gtk.VBox):
    def __init__(self, title):
        gtk.VBox.__init__(self)
        self.show()
        self.title_text = title

    def set_title(self, title):
        self.title_text = title

    def get_title(self):
        return self.title_text

    def get_tab_label(self):
        return gtk.Label(self.title_text)

    def on_close(self, w, tab):
        notebook = self.win.notebook
        page_number = notebook.page_num(tab)
        notebook.remove_page(page_number)

    def close(self):
        self.on_close(self, self)

class CloseTab(Tab):
    def __init__(self, title):
        Tab.__init__(self, title)
        self.close_button = self._prepare_close_button()
        self.close_button.connect("clicked", self.on_close, self)

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
        hbox.pack_start(gtk.Label(self.title_text))
        hbox.pack_start(self.close_button, False, False)
        hbox.show_all()
        return hbox

class WelcomeTab(CloseTab):
    def __init__(self, title):
        CloseTab.__init__(self, title)
        self.pack_start(gtk.Label("Welcome in simulator"))

class ProjectTab(Tab):
    def __init__(self, project):
        Tab.__init__(self, "Project")
        self.project = project
        self.project.project_tab = self
        self._create_content()

    def _create_content(self):
        glade_file = paths.GLADE_DIALOG_DIRECTORY + "project_tab.glade"
        self.builder = gtk.Builder()
        self.builder.add_from_file(glade_file)
        box = self.builder.get_object("vbox")
        tv = self.builder.get_object("treeview")
        tv.set_property("hover-selection", True)
        tv.set_property("enable-grid-lines", True)
        tv.set_rules_hint(True)
        self.treeview = tv
        self.liststore = self.builder.get_object("liststore")
        self.pack_start(box)
        self._connect_signals()

    def _connect_signals(self):
        handler = {
                   "on_add_button_clicked": lambda w: self.add_graph_file(),
                   "on_remove_button_clicked": lambda w: self.remove_graph_file(),
                   "on_run_sim_button_clicked": lambda w: self.run_simulations(),
                   "on_run_viz_button_clicked": lambda w: self.run_vizual_simulations(),
                   "selected_toggled": self.on_selected_toggled
                   }
        self.builder.connect_signals(handler)

    def load(self):
        algorithms = ["MyProcess", "SPINProcess"]
        combobox = self.builder.get_object("combobox")
        for alg in algorithms:
            combobox.append_text(alg)
        combobox.set_active(0)

        for filename in self.project.files:
            graph = self.project.get_graph(filename)
            if graph:
                nodes = graph.get_nodes_count()
                edges = graph.get_edges_count()
                self.liststore.append([False, filename, nodes, edges])
                info = "Added graph {0} nodes:{1}, edges:{2}"
                self.win.console.writeln(info.format(filename,
                                                     nodes,
                                                     edges))
            else:
                self.win.console.writeln("Graph file "
                                         + filename
                                         + " is corrupted")

    def on_selected_toggled(self, w, iter):
        self.liststore[iter][0] = not self.liststore[iter][0]

    def add_graph_file(self):
        file = xmld.XMLDialog.open_file()
        if file:
            added = self.project.add_graph_file(file)
            if added:
                try:
                    graph = self.project.get_graph(file)
                except Exception as ex:
                    self.win.console.writeln(file
                                             + " is corrupted",
                                             "err")
                    self.project.remove_graph_file(file)
                    return

                nodes = graph.get_nodes_count()
                edges = graph.get_edges_count()
                self.liststore.append([False, file, nodes, edges])
                info = "Added graph {0} nodes:{1}, edges:{2}"
                self.win.console.writeln(info.format(file,
                                                     nodes,
                                                     edges))

    def remove_graph_file(self):
        for row in self.liststore:
            if row[0]:
                self.win.console.writeln(row[1] + " removed from project")
                self.project.remove_graph_file(row[1])
                self.liststore.remove(row.iter)

    def run_simulations(self):
        process_type = self.builder.get_object("combobox").get_active_text()
        process_count = self.builder.get_object("process_num_button").get_value_as_int()
        sim_count = self.builder.get_object("sim_num_button").get_value_as_int()
        data = []
        try:
            for row in self.liststore:
                if row[0]:
                    filename = row[1]
                    graph = self.project.get_graph(filename)
                    data.append((filename, graph))

            sim_properties = {
                "sim_count": sim_count,
                "process_type": process_type,
                "process_count": process_count,
                "data": data
            }
            if len(data):
                self.win.create_tab(SimulationProgressTab("Simulation",
                                                          self.win,
                                                          self.project,
                                                          sim_properties))
        except Exception as ex:
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
                    visible_graph = self.project.get_visible_graph(row[1])
                    import simulationtab as st
                    title = "Viz. sim - " + ntpath.basename(row[1])
                    sim_tab = self.win.create_tab(st.VizualSimulationTab(title,
                                                                   visible_graph,
                                                                   self.win))
                    sim_tab.start()
                except Exception as ex:
                    self.win.console.writeln(ex.message, "err")

"""
class SimProgressBarTab(CloseTab):

    def __init__(self, title, simulator, window):
        CloseTab.__init__(self, title)
        self.simulator = simulator
        self.win = window
        self.progress_bar = progressbar.ProgressBar("")
        self.progress_bar.connect("tick", self.on_tick)
        self.progress_bar.connect("complete", self.on_complete)
        self.pack_start(self._create_content_panel(), False, False)
        #self.simulator.connect("end_simulation", lambda s: self.progress_bar.tick())
        self.progress_bar.start()

    def _create_content_panel(self):
        vbox = gtk.VBox()
        vbox.pack_start(gtk.Label("Simulation progress"), False, False)
        vbox.pack_start(self.progress_bar.get_progress_bar(), False, False)
        vbox.show_all()
        return vbox

    def on_complete(self):
        self.progress_bar.set_progressbar_text("Simulation completed...Gathering statistics")
        gtk.main_iteration()
        self.win.create_tab(PlotTab(self.get_title(), self.simulator))
        self.on_close(self, self)

    def on_tick(self, fraction):
        values = self.simulator.graph.nodes.values()
        nodes_count = len(values)
        curr_count = 0
        for node in values:
            if node.is_discovered():
                curr_count += 1

        self.progress_bar.set_progressbar_text("{0}/{1}".format(curr_count, nodes_count))
        new_val = curr_count / float(nodes_count)
        self.progress_bar.set_value(new_val)

    def on_close(self, w, tab):
        if self.simulator.is_running():
            self.simulator.stop()
        self.progress_bar.stop()
        CloseTab.on_close(self, w, tab)
"""

class SimulatorTab(CloseTab):
    def __init__(self, title, simulator):
        CloseTab.__init__(self, title)
        self.simulator = simulator
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_LEFT)
        sw.add_with_viewport(self.notebook)
        self.statistics = self._create_statistics()
        self.plot_stats = PlotStatistics(self)
        self.plot_stats.create_properties(self.statistics)
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
            add_plot_page(process_plot.get_widget(), process_plot.get_title())

        self.notebook.connect("switch-page", self.on_page_switch)
        self.show_all()

    def on_page_switch(self, notebook, page, num):
        if num > 0:
            tab = notebook.get_nth_page(num)
            if tab:
                selected_plot = tab.plot 
                selected_plot.draw()

    def _create_statistics(self):
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("Simulation results"), False, False)
        vbox.pack_start(hbox, False, False)
        return vbox

    def on_close(self, w, tab):
        for p in self.plots:
            p.dispose()
        CloseTab.on_close(self, w, tab)

class SimulationProgressTab(CloseTab):
    PROGRESS_BAR_REFRESH_TIME = 100

    def __init__(self, title, window, project, sim_properties):
        CloseTab.__init__(self, title)
        self.liststore = gtk.ListStore(str, int, str, float) # process type, progress, status, time
        self.simulators = []
        self.current_iter = -1
        self.win = window
        self.closed = False
        self.timer = timer.Timer(self.PROGRESS_BAR_REFRESH_TIME, self.on_timeout)
        self._prepare_data(sim_properties, project)
        self._create_content()
        self.start_next_sim()

    def _prepare_data(self, sim_properties, project):
        sim_count = sim_properties["sim_count"]
        process_count = sim_properties["process_count"]
        process_type = sim_properties["process_type"]
        data = sim_properties["data"]

        for i in xrange(sim_count):
            for file, graph in data:
                simulator = simulation.Simulation(graph)
                simulator.register_n_processes(process_type, process_count)
                process_info = "{0} - {1}({2})".format(ntpath.basename(file),
                                                      process_type,
                                                      process_count)
                self.liststore.append([process_info, 0, "PENDING", 0.0])
                self.simulators.append(simulator)

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
        if not self.closed and self.current_iter + 1 < len(self.simulators):
            self.current_iter += 1
            self.liststore[self.current_iter][2] = "In progress"
            self.timer.start()
            sim = self.simulators[self.current_iter]
            sim.connect("end_simulation", lambda s: self.on_sim_complete(s, self.current_iter))
            new_thread = threading.Thread(target = lambda: sim.start())
            new_thread.daemon = True
            try:
                new_thread.start()
            except Exception:
                sim.stop()
                self.win.console.write("LOW MEMORY", "err")

    def on_timeout(self):
        if self.closed:
            return False
        sim = self.simulators[self.current_iter]
        nodes_count = sim.graph.get_nodes_count()
        curr_nodes = sim.graph.get_discovered_nodes_count()
        new_val = curr_nodes / float(nodes_count)
        self.liststore[self.current_iter][1] = int(new_val * 100)
        if new_val >= 1.0:
            return False
        return True

    def on_sim_complete(self, sim, iter):
        status = sim.sim_status
        self.timer.stop()
        if not status:
            self.liststore[iter][2] = "Completed"
            self.liststore[iter][3] = sim.env.now
            self.liststore[iter][1] = 100
        else:
            self.liststore[iter][2] = status
            self.liststore[iter][3] = -1
            self.liststore[iter][1] = 0
        self.start_next_sim()

    def on_cancel(self):
        index = self.get_selected_row_index()
        if index > -1:
            sim = self.simulators[index]
            if sim.is_running():
                sim.stop()
            del sim

    def on_export(self):
        index = self.get_selected_row_index()
        if index > -1:
            if self.liststore[index][2] == "Completed":
                sim = self.simulators[index]
                new_file = csvd.CSVDialog.save_as_file()
                if new_file:
                    if not new_file.get_path().endswith(".csv"):
                        msgd.MessageDialog().error_dialog(self.win,
                            "File name has to end with .csv")
                        return
                    ex = exportmodule.CSVExportDataModule(sim)
                    ex.print_to_file(new_file)
                    msgd.MessageDialog().info_dialog(self.win,
                        "Data was successfully exported to " + new_file.get_path())

    def on_show_results(self):
        index = self.get_selected_row_index()
        if index > -1:
            if self.liststore[index][2] == "Completed":
                sim = self.simulators[index]
                title = self.liststore[index][0]
                simulator_tab = SimulatorTab(title + "- Detail", sim)
                self.win.create_tab(simulator_tab)
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

    def on_close(self, w, tab):
        if not self.closed:
            self.timer.stop()
            for sim in self.simulators:
                if sim.is_running():
                    sim.stop()
                del sim.env
                del sim.graph
                del sim
                    
            self.closed = True
            del self.simulators
        CloseTab.on_close(self, w, tab)
