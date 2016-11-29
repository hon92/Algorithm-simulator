import gtk
import paths
import ntpath
import plot
import exportmodule
import settings
import simulationcontroller as sc
import gladeloader as gl
import numpy as np
from misc import timer
from gui import worker
from sim import simulation
from gui.dialogs import dialog
from canvas import Canvas
from nodeselector import NodeSelector
from gui import statistics
from sim import processfactory as pf
from misc import progressbar


class Tab(gtk.VBox):
    def __init__(self, window, title):
        gtk.VBox.__init__(self)
        self.win = window
        self.label = gtk.Label(title)
        self.show()

    def set_title(self, title):
        self.label.set_text(title)

    def get_title(self):
        return self.label.get_text()

    def get_tab_label(self):
        return self.label

    def close(self):
        self.win.remove_tab(self)

    def is_project_independent(self):
        return False

    def pre_build(self):
        pass

    def build(self):
        pass

    def post_build(self):
        pass

    def build_content(self):
        widget = self.build()
        if widget:
            self.pack_start(widget)

    def create(self):
        self.pre_build()
        self.build_content()
        self.post_build()
        self.show_all()


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

    def build(self):
        msg = "Welcome in tool simulating \ndistributed algorithms for exploring state space."
        return gtk.Label(msg)

    def is_project_independent(self):
        return True


class ProjectTab(Tab):
    def __init__(self, window, project):
        Tab.__init__(self, window, "Project")
        self.project = project
        self.win.set_title(project.get_name())
        self.params = []
        pf.process_factory.connect("algorithm_added", self._on_algorithm_added)
        pf.process_factory.connect("algorithm_remove", self._on_algorithm_remove)

    def build(self):
        builder = gl.GladeLoader("project_tab").load()
        self.box = builder.get_object("vbox")
        self.treeview = builder.get_object("treeview")
        self.treeview.set_property("hover-selection", True)
        self.liststore = builder.get_object("liststore")
        self.toggle_render = builder.get_object("cellrenderertoggle")
        self.add_button = builder.get_object("add_button")
        self.remove_button = builder.get_object("remove_button")
        self.sim_button = builder.get_object("run_sim_button")
        self.viz_button = builder.get_object("run_viz_button")
        self.combobox = builder.get_object("combobox")
        self.model_combobox = builder.get_object("model_combobox")
        self.process_num_button = builder.get_object("process_num_button")
        self.sim_num_button = builder.get_object("sim_num_button")
        self.alg_description = builder.get_object("alg_description")
        self.remove_old_checkbutton = builder.get_object("remove_old_checkbutton")
        self.parameters_box = builder.get_object("parameters_vbox")
        return self.box

    def post_build(self):
        self._connect_signals()
        self.init()

    def _connect_signals(self):

        def on_selected_toggle(w, i):
            self.liststore[i][0] = not self.liststore[i][0]

        def show_params(params):
            self.params = []
            def rm(w):
                self.parameters_box.remove(w)
            self.parameters_box.foreach(rm)

            if len(params) == 0:
                hb = gtk.HBox()
                hb.pack_start(gtk.Label("No parameters"))
                self.parameters_box.pack_start(hb)
                self.parameters_box.show_all()
                return

            for param, val in params.iteritems():
                v = val[0]
                p_type = val[1]
                hbox = gtk.HBox()
                hbox.pack_start(gtk.Label(param))
                entry = gtk.Entry()
                entry.set_text(str(v))
                hbox.pack_start(entry)
                hbox.show_all()
                self.parameters_box.pack_start(hbox)
                self.params.append((param, entry, p_type))

        def on_alg_change(w):
            active_text = w.get_active_text()
            if active_text:
                desc = pf.process_factory.get_process_description(active_text)
                params = pf.process_factory.get_process_parameters(active_text)
                show_params(params)
                self.alg_description.set_text(desc)

        self.toggle_render.connect("toggled", on_selected_toggle)
        self.add_button.connect("clicked", lambda w: self.add_graph_file())
        self.remove_button.connect("clicked", lambda w: self.remove_graph_file())
        self.sim_button.connect("clicked", self.on_sim_button_clicked)
        self.viz_button.connect("clicked", self.on_viz_sim_button_clicked)
        self.combobox.connect("changed", on_alg_change)

    def init(self):
        algorithms = pf.process_factory.get_processes_names()
        for alg_name in algorithms:
            self.combobox.append_text(alg_name)
        if len(algorithms) > 0:
            self.combobox.set_active(0)

        models_names = pf.process_factory.get_models_names()
        for model_name in models_names:
            self.model_combobox.append_text(model_name)
        if len(models_names) > 0:
            self.model_combobox.set_active(0)

        def on_query_tooltip(combobox, x, y, keyboard_mode, tooltip):
            selected_model = combobox.get_active_text()
            if selected_model:
                desc = pf.process_factory.get_model_description(selected_model)
                if desc:
                    tooltip.set_text(desc)
            return True

        self.model_combobox.set_property("has-tooltip", True)
        self.model_combobox.connect("query-tooltip", on_query_tooltip)
        for filename in self.project.get_files():
            self.add_graph(filename)

    def _on_algorithm_added(self, process_factory, alg):
        self.combobox.append_text(alg.NAME)
        if self.combobox.get_active() == -1:
            self.combobox.set_active(0)

    def _on_algorithm_remove(self, process_factory, alg):
        model = self.combobox.get_model()
        for row in model:
            if row[0] == alg.NAME:
                self.combobox.remove_text(row.path[0])
                break

    def add_graph(self, filename):
        graph_manager = self.project.graph_manager
        graph = graph_manager.get_graph(filename)
        if graph:
            nodes = graph.get_nodes_count()
            edges = graph.get_edges_count()
            self.liststore.append([False, filename, nodes, edges])
            info = "Graph '{0}' added to project"
            self.win.console.writeln(info.format(filename))

    def add_graph_file(self):
        graph_file = dialog.Dialog.get_factory("xml").open("Open graph file")

        if graph_file:
            added = self.project.add_file(graph_file)
            if added:
                self.add_graph(graph_file)

    def remove_graph_file(self):
        for row in self.liststore:
            if row[0]:
                msg = "'{0}' was removed from project"
                self.win.console.writeln(msg.format(row[1]))
                self.project.remove_file(row[1])
                self.liststore.remove(row.iter)

    def on_sim_button_clicked(self, w):
        files = self.get_selected_files()
        if len(files) == 0:
            return
        process_count = self.get_process_count()
        process_type = self.get_process_type()
        if not process_type:
            return
        model = self.get_model()
        if not model:
            return
        sim_count = self.get_simulations_count()
        remove_previous = self.remove_previous()
        try:
            arguments = self.get_arguments()
        except Exception as ex:
            err_msg = "Algorithm parameter type error: {0}".format(ex.message)
            self.win.console.writeln(err_msg, "err")
            return

        self.run_simulations(files,
                            process_type,
                            process_count,
                            sim_count,
                            model,
                            arguments,
                            remove_previous)

    def run_simulations(self,
                        files,
                        process_type,
                        process_count,
                        sim_count,
                        model,
                        arguments = None,
                        remove_previous = False):
        simulations_tab = self.project.get_simulations_tab()
        if remove_previous:
            simulations_tab.clear()

        graph_manager = self.project.graph_manager
        for filename in files:
            graph = graph_manager.get_graph(filename)
            for _ in xrange(sim_count):
                sim = simulation.Simulation(process_type,
                                            process_count,
                                            graph,
                                            model,
                                            arguments)
                simulations_tab.add_simulation(sim)
        self.win.switch_to_tab(simulations_tab)

    def on_viz_sim_button_clicked(self, w):
        lines = [(row[1], int(row[2])) for row in self.liststore if row[0]]
        if len(lines) == 0:
            return

        process_count = self.get_process_count()
        process_type = self.get_process_type()
        if not process_type:
            return

        model = self.get_model()
        if not model:
            return

        try:
            arguments = self.get_arguments()
        except Exception as ex:
            err_msg = "Algorithm parameter type error: {0}".format(ex.message)
            self.win.console.writeln(err_msg, "err")
            return

        max_nodes_count = settings.get("MAX_VISIBLE_GRAPH_NODES")
        for filename, nodes_count in lines:
            if nodes_count > max_nodes_count:
                err_text = "Graph {0} was skipped because is too big" + \
                           " (max graph nodes count is {1})"
                err_text = err_text.format(filename, str(max_nodes_count))
                self.win.console.writeln(err_text, "err")
                continue
            self.run_visual_simulation(filename, process_type, process_count, model, arguments)

    def run_visual_simulation(self,
                              filename,
                              process_type,
                              process_count,
                              model,
                              arguments = None):
        CANVAS_MAX_SIZE = 5000
        name = ntpath.basename(filename)
        title = "{0} - {1}({2})".format(name, process_type, process_count)
        graph = self.project.graph_manager.get_visual_graph(filename)
        if graph.width > CANVAS_MAX_SIZE or graph.height > CANVAS_MAX_SIZE:
            err_text = "Graph {0} was skipped because is too big" + \
                       " for drawing on canvas"
            err_text = err_text.format(filename)
            self.win.console.writeln(err_text, "err")
            return

        sim = simulation.VisualSimulation(process_type, process_count, graph, model, arguments)
        self.win.create_tab(VisualSimulationTab(self.win,
                                                title,
                                                sim))

    def get_process_count(self):
        return self.process_num_button.get_value_as_int()

    def get_process_type(self):
        return self.combobox.get_active_text()

    def get_simulations_count(self):
        return self.sim_num_button.get_value_as_int()

    def remove_previous(self):
        return self.remove_old_checkbutton.get_active()

    def get_model(self):
        model_name = self.model_combobox.get_active_text()
        if not model_name:
            return None
        return pf.process_factory.get_model(model_name)

    def get_selected_files(self):
        return [row[1] for row in self.liststore if row[0]]

    def get_arguments(self):
        arguments = {}
        for param_key, param_entry, p_type in self.params:
            val = p_type(param_entry.get_text())
            arguments[param_key] = val
        return arguments


class SimulationDetailTab(CloseTab):
    def __init__(self, window, title, simulation):
        CloseTab.__init__(self, window, title)
        self.simulation = simulation
        self.plots = []

    def build(self):
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_LEFT)
        sw.add_with_viewport(self.notebook)
        return sw

    def post_build(self):
        self.stats_vbox = self._create_statistics()
        self.notebook.append_page(self.stats_vbox, gtk.Label("Results"))
        self.create_plots()

    def create_plots(self):
        def add_plot_page(widget, title):
            self.notebook.append_page(widget, gtk.Label(title))
            self.plots.append(widget.plot)

        def add_process_plot_page(notebook, widget, title):
            notebook.append_page(widget, gtk.Label(title))
            self.plots.append(widget.plot)

        processes = self.simulation.ctx.processes
        memory_usage_plot = plot.MemoryUsagePlot(processes)
        storage_usage_plot = plot.StorageMemoryUsagePlot(processes)
        processes_plot = plot.ProcessesLifePlot(processes)
        discovered_plot = plot.DiscoveredPlot(processes)
        cummulative_plot = plot.CummulativeSumPlot(processes)
        calculated_plot = plot.CalculatedPlot(processes)

        add_plot_page(memory_usage_plot.get_widget_with_navbar(self.win),
                      memory_usage_plot.get_title())
        add_plot_page(storage_usage_plot.get_widget_with_navbar(self.win),
                      storage_usage_plot.get_title())

        add_plot_page(processes_plot.get_widget_with_navbar(self.win), processes_plot.get_title())
        add_plot_page(discovered_plot.get_widget_with_navbar(self.win), discovered_plot.get_title())
        add_plot_page(cummulative_plot.get_widget_with_navbar(self.win), cummulative_plot.get_title())
        add_plot_page(calculated_plot.get_widget_with_navbar(self.win), calculated_plot.get_title())

        for process in self.simulation.ctx.processes:
            notebook = gtk.Notebook()

            pr_mem_usage_plot = plot.ProcessMemoryUsagePlot(process)
            pr_calc_edge_plot = plot.ProcessCalculatedPlot(process)
            pr_disc_edge_plot = plot.ProcessDiscoveredEdgesPlot(process)
            pr_com_plot = plot.ProcessCommunicationPlot(process)
            add_process_plot_page(notebook,
                                  pr_mem_usage_plot.get_widget_with_navbar(self.win),
                                  pr_mem_usage_plot.get_title())
            add_process_plot_page(notebook,
                                  pr_calc_edge_plot.get_widget_with_navbar(self.win),
                                  pr_calc_edge_plot.get_title())
            add_process_plot_page(notebook,
                                  pr_disc_edge_plot.get_widget_with_navbar(self.win),
                                  pr_disc_edge_plot.get_title())
            add_process_plot_page(notebook,
                                  pr_com_plot.get_widget_with_navbar(self.win),
                                  pr_com_plot.get_title())
            notebook.pr_notebook_loaded = False
            self.notebook.append_page(notebook,
                                      gtk.Label("Detail of process {0}".format(process.id)))

        self.notebook.connect("switch-page", self.on_page_switch)

    def on_page_switch(self, notebook, page, num):
        new_tab = notebook.get_nth_page(num)
        if new_tab:
            if hasattr(new_tab, "plot"):
                new_tab.plot.draw()
            elif hasattr(new_tab, "pr_notebook_loaded"):
                if not new_tab.pr_notebook_loaded:
                    new_tab.pr_notebook_loaded = True
                    new_tab.connect("switch-page", self.on_page_switch)
                    if new_tab.get_n_pages() > 0:
                        self.on_page_switch(new_tab, None, 0)

    def _create_statistics(self):
        vbox = gtk.VBox()
        builder = gl.GladeLoader("tree_statistics").load()
        stat_widget = builder.get_object("vbox")
        info_store = builder.get_object("infostore")
        statistics.SimulationStatistics(info_store, self.simulation).init_properties()
        vbox.pack_start(stat_widget)
        return vbox

    def close(self):
        for p in self.plots:
            p.dispose()
        CloseTab.close(self)


"""
class SimulationProgressTab(CloseTab):
    PROGRESS_BAR_REFRESH_TIME = 100
    RUNNING = "In progress"
    CANCELED = "Canceled"
    WAITING = "Pending"
    COMPLETED = "Completed"

    NAME_COL = 0
    PROGRESS_COL = 1
    STATUS_COL = 2
    TIME_COL = 3
    FILENAME_COL = 4
    ORDER_COL = 5

    def __init__(self, window, title, project, sim_properties):
        CloseTab.__init__(self, window, title)
        self.project = project
        self.sim_props = sim_properties
        self.opened_tabs = []
        self.current_iter = None
        self.current_order = 0
        self.completed_simulations = {}
        self.used_graphs = {}
        self.closed = False
        self.finished = False

        self.timer = timer.Timer(self.PROGRESS_BAR_REFRESH_TIME, self.on_timeout)
        self.worker = worker.SimWorker()
        self.worker.setDaemon(True)
        self.worker.add_callback(lambda s: gtk.idle_add(self.on_sim_complete, s))
        self.worker.add_error_callback(lambda s, msg: gtk.idle_add(self.on_sim_error, s, msg))

    def build(self):
        builder = gl.GladeLoader("simulation_progress_view").load()
        vbox = builder.get_object("vbox")
        self.treeview = builder.get_object("treeview")
        # model structure -> process type, progress, status, time, filename, order
        self.liststore = builder.get_object("liststore")

        self.name_col = builder.get_object("name_column")
        self.progress_col = builder.get_object("progress_column")
        self.status_col = builder.get_object("status_column")
        self.time_col = builder.get_object("time_column")

        self.name_col.set_sort_column_id(-1)
        self.progress_col.set_sort_column_id(-1)
        self.status_col.set_sort_column_id(-1)
        self.time_col.set_sort_column_id(-1)

        show_button = builder.get_object("show_button")
        export_button = builder.get_object("export_button")
        cancel_button = builder.get_object("cancel_button")

        def create_button(button, icon, tooltip, callback):
            image = gtk.Image()
            image.set_from_file(paths.ICONS_PATH + icon)
            button.add(image)
            button.set_tooltip_text(tooltip)
            button.connect("clicked", lambda w: callback())
            button.show_all()
            return button

        show_button = create_button(show_button,
                                    "Show Property-24.png",
                                    "Show results",
                                    self.on_show_results)

        export_button = create_button(export_button,
                                      "CSV-24.png",
                                      "Export data to CSV",
                                      self.on_export)

        cancel_button = create_button(cancel_button,
                                      "Close Window-24.png",
                                      "Cancel simulation",
                                      self.on_cancel)
        return vbox

    def post_build(self):
        def col_clicked(treeview_column):
            if self.finished:
                self.name_col.set_sort_column_id(self.NAME_COL)
                self.progress_col.set_sort_column_id(self.PROGRESS_COL)
                self.status_col.set_sort_column_id(self.STATUS_COL)
                self.time_col.set_sort_column_id(self.TIME_COL)

        self.name_col.connect("clicked", col_clicked)
        self.progress_col.connect("clicked", col_clicked)
        self.status_col.connect("clicked", col_clicked)
        self.time_col.connect("clicked", col_clicked)
        self.prepare()
        self.run()

    def prepare(self):
        sim_count = self.sim_props["sim_count"]
        process_count = self.sim_props["process_count"]
        process_type = self.sim_props["process_type"]
        files = self.sim_props["files"]

        for filename in files:
            self.used_graphs[filename] = self.project.graph_manager.get_graph(filename)

        order = 0
        for _ in xrange(sim_count):
            for filename in files:
                graph = self.used_graphs[filename]
                simulator = simulation.Simulation(process_type, process_count, graph)
                
                simulator.register_n_processes(process_type, process_count)
                for process in simulator.processes:
                    process.connect("log", self.log_message)
                process_info = "{0} - {1}({2})".format(ntpath.basename(filename),
                                                      process_type,
                                                      process_count)
                
                order += 1
                self.liststore.append(["process_info", 0, self.WAITING, 0.0, filename, order])
                self.worker.put(simulator)

    def run(self):
        self.worker.start()
        self.start_next_sim()

    def log_message(self, msg, tag):
        self.win.console.writeln(msg, tag)

    def get_next_row(self):
        for row in self.liststore:
            order = row.model.get_value(row.iter, self.ORDER_COL)
            if order > self.current_order:
                self.current_order = order
                return row.iter
        self.finished = True
        return None

    def start_next_sim(self):
        if self.closed:
            return

        self.set_title("Simulation ({0}/{1})".format(self.current_order,
                                                     self.sim_props["sim_count"] * 
                                                     len(self.sim_props["files"])))

        self.timer.stop()
        self.current_iter = self.get_next_row()
        if not self.current_iter:
            return

        self.liststore.set(self.current_iter, self.STATUS_COL, self.RUNNING)
        self.timer.start()

    def on_timeout(self):
        sim = self.worker.task_in_progress
        if not sim:
            return False
        nodes_count = sim.graph.get_nodes_count()
        curr_nodes = sim.graph.get_discovered_nodes_count()
        new_val = curr_nodes / float(nodes_count)
        if new_val > 1.0:
            self.log_message("Progress value is bigger then 1.0", "warn")
        self.liststore.set(self.current_iter, self.PROGRESS_COL, int(new_val * 100))
        if new_val >= 1.0:
            return False
        return True

    def on_sim_complete(self, sim):
        status = sim.sim_status
        if not status:
            self.liststore.set(self.current_iter,
                               self.PROGRESS_COL, 100,
                               self.STATUS_COL, self.COMPLETED,
                               self.TIME_COL, sim.env.now)
            self.completed_simulations[self.current_order] = sim
        else:
            self.liststore.set(self.current_iter,
                               self.PROGRESS_COL, 0,
                               self.STATUS_COL, self.CANCELED,
                               self.TIME_COL, 0)
        self.start_next_sim()

    def on_sim_error(self, sim, msg):
        self.liststore.set(self.current_iter,
                               self.PROGRESS_COL, 0,
                               self.STATUS_COL, self.CANCELED,
                               self.TIME_COL, 0)
        error_msg = "{0}: {1}".format(self.liststore.get_value(self.current_iter, self.NAME_COL), msg)
        self.log_message(error_msg, "err")
        self.start_next_sim()

    def on_cancel(self):
        iter = self.get_selected_row_iter()
        if iter:
            if self.liststore.get_value(iter, self.STATUS_COL) == self.RUNNING:
                sim = self.worker.task_in_progress
                if sim:
                    sim.stop()

    def on_export(self):
        iter = self.get_selected_row_iter()
        if iter:
            if self.liststore.get_value(iter, self.STATUS_COL) == self.COMPLETED:
                order = self.liststore.get_value(iter, self.ORDER_COL)
                if order not in self.completed_simulations:
                    return

                sim = self.completed_simulations[order]
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
        iter = self.get_selected_row_iter()
        if iter:
            if self.liststore.get_value(iter, self.STATUS_COL) == self.COMPLETED:
                order = self.liststore.get_value(iter, self.ORDER_COL)
                if order in self.completed_simulations:
                    sim = self.completed_simulations[order]
                    title = self.liststore.get_value(iter, self.NAME_COL)
                    filename = self.liststore.get_value(iter, self.FILENAME_COL)
                    simulator_tab = SimulatorTab(self.win,
                                                 title + "- Detail",
                                                 filename,
                                                 sim)
                    self.win.create_tab(simulator_tab)
                    self.opened_tabs.append(simulator_tab)

    def get_selected_row_iter(self):
        tree_selection = self.treeview.get_selection()
        if tree_selection:
            model, rows = tree_selection.get_selected_rows()
            if model and rows:
                if len(rows):
                    return model.get_iter(rows[0][0])
        return None

    def close(self):
        self.closed = True
        self.timer.stop()
        self.worker.interrupt_current_task()
        self.worker.quit()
        for tab in self.opened_tabs:
            tab.close()
        for f in self.used_graphs:
            self.project.graph_manager.return_graph(f, self.used_graphs[f])
        CloseTab.close(self)
"""

class VisualSimulationTab(CloseTab):

    CANVAS_BACKGROUND_COLOR = (247, 207, 45)

    def __init__(self, window, title, simulation):
        CloseTab.__init__(self, window, title)
        self.simulation = simulation
        self.anim_plot = plot.VizualSimPlotAnim()
        self.node_selector = NodeSelector(self.simulation.ctx.graph)

    def build(self):
        builder = gl.GladeLoader("visual_sim_tab").load()
        vbox = builder.get_object("vbox")
        self.toolbar = builder.get_object("toolbar")
        self.statusbar = builder.get_object("statusbar")
        self.properties_store = builder.get_object("propertystore")
        self.info_store = builder.get_object("infostore")
        self.status_ctx = self.statusbar.get_context_id("Simulation state")

        canvas_container = builder.get_object("canvascontainer")
        canvas_container.pack_start(self.init_canvas())

        self.marker_button = builder.get_object("markerbutton")
        self.navbar_button = builder.get_object("navbarbutton")
        self.time_button = builder.get_object("timebutton")
        self.step_button = builder.get_object("stepbutton")

        plotvbox = builder.get_object("plotvbox")
        plotvbox.pack_start(self.anim_plot.create_widget(self.win))
        return vbox

    def post_build(self):
        self.marker_button.set_active(self.anim_plot.has_marker())
        self.navbar_button.set_active(self.anim_plot.has_navbar())
        if self.anim_plot.get_unit() == "time":
            self.time_button.set_active(True)
        else:
            self.step_button.set_active(True)
        self.marker_button.connect("toggled", self.on_marker_button_toggle)
        self.navbar_button.connect("toggled", self.on_navbar_button_toggle)
        self.time_button.connect("toggled", self.on_unit_change, "time")
        self.step_button.connect("toggled", self.on_unit_change, "step")
        self.controller = sc.SimulationController(self, self.toolbar)
        self.state_stats = statistics.StateStatistics(self.properties_store)
        self.sim_stats = statistics.SimulationStatistics(self.info_store,
                                                         self.simulation)
        self.controller.run()

    def init_canvas(self):
        canvas = Canvas()
        canvas.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        c = self.CANVAS_BACKGROUND_COLOR
        canvas.modify_bg(gtk.STATE_NORMAL,
                         gtk.gdk.Color(c[0] * 256,c[1] * 256,c[2] * 256))
        canvas.connect("configure_event", lambda w, e: self.redraw())
        canvas.connect("button_press_event", lambda w, e: self.on_mouse_click(e))
        graph = self.simulation.ctx.graph
        canvas.set_size_request(graph.width, graph.height)
        self.canvas = canvas
        return canvas

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
        self.canvas.set_color(*self.CANVAS_BACKGROUND_COLOR)
        self.canvas.draw_rectangle(0,
                                   0,
                                   self.canvas.allocation.width,
                                   self.canvas.allocation.height,
                                   True)
        ctx = self.simulation.ctx
        ctx.graph.draw(self.canvas, ctx.graph_stats)
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
        gs = self.simulation.ctx.graph_stats
        if node:
            gs.set_selected_node(node.id)
            self.update_node_info(node)
        else:
            gs.set_selected_node(None)
            self.state_stats.reset()
        self.redraw()

    def on_mouse_click(self, e):
        if e.button != 1:
            return

        zoom = self.canvas.get_zoom()
        selected_node = self.node_selector.get_node_at(int(e.x), int(e.y), zoom)
        self.switch_selected_node(selected_node)

    def update_node_info(self, node):
        self.state_stats.update(node, self.simulation)

    def close(self):
        self.controller.stop()
        self.anim_plot.dispose()
        self.canvas.dispose()
        CloseTab.close(self)


class SettingsTab(CloseTab):
    def __init__(self, window):
        CloseTab.__init__(self, window, "Settings")

    def build(self):
        hbox = gtk.HBox()
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_LEFT)
        self.notebook.set_scrollable(True)
        hbox.pack_start(self.notebook)

        def add_setting_page(setting_page):
            setting_page.connect("apply", self.on_settings_apply)
            setting_page.connect("restore", self.on_settings_restore)
            self.notebook.append_page(setting_page.build(), setting_page.get_label())

        general_settings = settings.GeneralSettingPage()
        simulation_settings = settings.SimulationSettingPage()
        visual_sim_settings = settings.VisualSimSettingPage()
        scripts_settings = settings.ScriptSettingPage()

        add_setting_page(general_settings)
        add_setting_page(simulation_settings)
        add_setting_page(visual_sim_settings)
        add_setting_page(scripts_settings)
        return hbox

    def is_project_independent(self):
        return True

    def on_settings_apply(self):
        self.win.console.writeln("Settings saved")

    def on_settings_restore(self):
        self.win.console.writeln("Settings restored")


class SimulationsTab(Tab):

    RUNNING = "In progress"
    CANCELED = "Canceled"
    WAITING = "Pending"
    COMPLETED = "Completed"
    ERROR = "Error"

    def __init__(self, window, project):
        Tab.__init__(self, window, "Simulations")
        self.project = project
        self.timer = timer.Timer(100, self.on_timeout)
        self.worker = worker.SimWorker(self.on_simulation_start,
                                       self.on_simulation_complete,
                                       self.on_simulation_error)

        self.worker.start()
        self.current = 0
        self.current_sim = None
        self.completed_simulations = {}

    def build(self):
        builder = gl.GladeLoader("simulations_tab").load()
        vbox = builder.get_object("vbox")
        self.liststore = builder.get_object("liststore")
        self.treeview = builder.get_object("treeview")

        show_button = builder.get_object("detail_button")
        export_button = builder.get_object("export_sim_button")
        cancel_button = builder.get_object("cancel_button")
        show_summary_button = builder.get_object("show_summary_button")
        export_simulations_button = builder.get_object("export_simulations_button")
        clear_button = builder.get_object("clear_button")

        def create_button(button, icon, label, tooltip, callback):
            image = gtk.Image()
            image.set_from_file(paths.ICONS_PATH + icon)
            hbox = gtk.HBox()
            hbox.pack_start(image, False)
            hbox.pack_start(gtk.Label(label))
            button.add(hbox)
            button.set_tooltip_text(tooltip)
            button.connect("clicked", lambda w: callback())
            button.show_all()
            return button

        create_button(show_button,
                      "Show Property-24.png",
                      "Simulation detail",
                      "Show results",
                      self.on_sim_detail)

        create_button(export_button,
                      "CSV-24.png",
                      "Simulation export",
                      "Export data to CSV",
                      self.on_sim_export)

        create_button(cancel_button,
                      "Close Window-24.png",
                      "Cancel simulation",
                      "Cancel simulation",
                      self.on_cancel)

        create_button(show_summary_button,
                      "Pie Chart-24.png",
                      "Show summary",
                      "Show summary of all simulations",
                      self.on_show_summary)

        create_button(export_simulations_button,
                      "CSV-24.png",
                      "Export simulations",
                      "Export all simulations to CSV",
                      self.on_simulations_export)


        create_button(clear_button,
                      "Delete-24 (1).png",
                      "Clear simulations",
                      "Stop and clear all simulations from list",
                      self.on_clear)
        return vbox

    def _update_title(self):
        self.set_title("Simulations {0} / {1} ".format(self.current, len(self.liststore)))

    def clear(self):
        self.worker.clear_tasks()
        self.worker.interrupt()
        self.completed_simulations = {}
        self.liststore.clear()
        self.current = 0
        self._update_title()

    def get_iter_at(self, row):
        try:
            return self.liststore.get_iter(row)
        except Exception:
            return None

    def on_timeout(self):
        if not self.current_sim:
            return False
        gs = self.current_sim.ctx.graph_stats
        nodes_count = gs.get_nodes_count()
        discovered_nodes_count = gs.get_discovered_nodes_count()
        new_val = discovered_nodes_count / float(nodes_count)

        if new_val == 1.0:
            return False

        iter = self.get_iter_at(self.current)
        if iter:
            self.liststore[iter][3] =  int(new_val * 100)
            self.liststore[iter][4] = self.RUNNING
            return True
        else:
            return False

    def add_simulation(self, simulation):
        self.liststore.append([simulation.ctx.graph.filename,
                               simulation.get_process_type(),
                               simulation.get_process_count(),
                               0,
                               self.WAITING,
                               0,
                               0])
        self.worker.put(simulation)
        self._update_title()

    def on_simulation_start(self, simulation):
        self.current_sim = simulation
        self.timer.start()

        def write_output(msg, tag):
            self.win.console.writeln(msg, tag)

        for pr in simulation.ctx.processes:
            pr.connect("log", write_output)

    def on_simulation_complete(self, simulation):
        self.timer.stop()
        self.current_sim = None
        mm = simulation.ctx.monitor_manager
        mem_monitor = mm.get_monitor("GlobalMemoryMonitor")
        memory_peak = 0
        if mem_monitor:
            mem_usage_entry = "memory_usage"
            data = mem_monitor.collect([mem_usage_entry])
            for _, storage_size in data[mem_usage_entry]:
                if storage_size > memory_peak:
                    memory_peak = storage_size

        self.completed_simulations[self.current] = simulation
        iter = self.get_iter_at(self.current)
        if iter:
            self.liststore[iter][3] = 100
            self.liststore[iter][4] = self.COMPLETED
            self.liststore[iter][5] = simulation.ctx.env.now
            self.liststore[iter][6] = memory_peak
        self.current += 1
        self._update_title()

    def on_simulation_error(self, error_message):
        self.timer.stop()
        graph_file = ntpath.basename(self.current_sim.ctx.graph.filename)
        pr_count = self.current_sim.get_process_count()
        pr_type = self.current_sim.get_process_type()
        status_text = self.CANCELED
        self.current_sim = None

        if error_message != self.CANCELED:
            err_msg = "Simulation {0} - {1}({2}) was interrupted by error {3}"
            self.win.console.writeln(err_msg.format(graph_file,
                                                    pr_type,
                                                    pr_count,
                                                    error_message),
                                                    "err")
            status_text = self.ERROR

        iter = self.get_iter_at(self.current)
        if iter:
            self.liststore[iter][3] = 0
            self.liststore[iter][4] = status_text
            self.liststore[iter][5] = 0
            self.liststore[iter][6] = 0
        self.current += 1
        self._update_title()

    def get_selected_row_iter(self):
        tree_selection = self.treeview.get_selection()
        if tree_selection:
            model, rows = tree_selection.get_selected_rows()
            if model and rows:
                if len(rows):
                    return model.get_iter(rows[0][0])
        return None

    def close(self):
        self.worker.quit()
        self.timer.stop()
        Tab.close(self)

    def on_sim_detail(self):
        iter = self.get_selected_row_iter()
        if iter:
            if self.liststore[iter][4] == self.COMPLETED:
                p = self.liststore[iter]
                sim = self.completed_simulations[p.path[0]]
                filename = self.liststore[iter][0]
                name = ntpath.basename(filename)
                process_type = self.liststore[iter][1]
                process_count = self.liststore[iter][2]
                tab_title = "{0} - {1}({2})".format(name,
                                                    process_type,
                                                    process_count)

                simulator_tab = SimulationDetailTab(self.win,
                                                    tab_title,
                                                    sim)
                self.win.create_tab(simulator_tab)

    def on_sim_export(self):
        iter = self.get_selected_row_iter()
        if iter:
            if self.liststore[iter][4] == self.COMPLETED:
                p = self.liststore[iter]
                sim = self.completed_simulations[p.path[0]]
                new_file = dialog.Dialog.get_factory("csv").save_as("Save simulation detail as")
                if new_file:
                    ex = exportmodule.CSVExportDataModule(new_file, sim)
                    try:
                        ex.print_to_file()
                        msg = "Data was exported to '{0}'"
                        self.win.console.writeln(msg.format(new_file))
                    except IOError as ex:
                        msg = "Export data to file '{0}' failed"
                        self.win.console.writeln(msg.format(new_file), "err")

    def on_simulations_export(self):
        if len(self.completed_simulations) == 0:
            return

        new_file = dialog.Dialog.get_factory("csv").save_as("Save completed simulations as")
        if new_file:
            lines = []
            lines.append("Filename;Algorithm;Process count;Time;Memory peak;\n")
            for row in self.liststore:
                if row[4] != self.COMPLETED:
                    continue
                filename = row[0]
                algorithm = row[1]
                pr_count = str(row[2])
                time = str(row[5])
                memory = str(row[6])
                lines.append(filename + ";" +
                             algorithm + ";" +
                             pr_count + ";" +
                             time + ";" +
                             memory + ";\n")

            with open(new_file, "w") as output:
                output.write("".join(lines))
                output.flush()

            msg = "Completed simulation was exported to {0}"
            self.win.console.writeln(msg.format(new_file))

    def on_cancel(self):
        iter = self.get_selected_row_iter()
        if iter:
            if self.liststore[iter][4] == self.RUNNING:
                if self.current_sim:
                    self.current_sim.stop()

    def on_clear(self):
        self.clear()

    def on_show_summary(self):
        if len(self.completed_simulations) == 0:
            return
        self.win.create_tab(SummaryTab(self.win, self.completed_simulations))


class SummaryTab(CloseTab):
    def __init__(self, window, simulations):
        CloseTab.__init__(self, window, "Summary tab")
        self.simulations = simulations.values()
        self.plots = []

    def build(self):
        builder = gl.GladeLoader("summary_tab").load()
        vbox = builder.get_object("vbox")
        self.notebook = builder.get_object("notebook")
        self.time_button = builder.get_object("time_rad_button")
        self.memory_button = builder.get_object("memory_rad_button")
        self.time_button.connect("toggled", self.on_type_change, "time")
        self.memory_button.connect("toggled", self.on_type_change, "memory")
        self.time_button.set_active(True)
        return vbox

    def _remove_tabs(self):
        for p in self.plots:
            p.dispose()
        self.plots = []
        tabs_count = self.notebook.get_n_pages()
        for i in xrange(tabs_count):
            self.notebook.remove_page(i)

    def on_type_change(self, button, name):
        if name not in ["time", "memory"]:
            raise Exception("Unknown radio button type")

        self._remove_tabs()
        groups = self._get_groups()
        if len(groups) == 0:
            return

        filenames = set()
        for s in self.simulations:
            filenames.add(s.ctx.graph.filename)

        for filename in filenames:
            data = []
            ticks = []
            for g in groups:
                if g.filename == filename:
                    if name == "memory":
                        data.append(list(g.memory))
                    else:
                        data.append(list(g.times))
                    ticks.append(g.get_label())

            if name == "memory":
                summary_plot = plot.MemorySummaryPlot(data, ticks)
            else:
                summary_plot = plot.TimeSummaryPlot(data, ticks)
            summary_plot.draw()
            self.plots.append(summary_plot)
            summ_widget = summary_plot.get_widget_with_navbar(self.win)
            self.notebook.append_page(summ_widget, gtk.Label(ntpath.basename(filename)))
        self.notebook.show_all()

    def _get_groups(self):
        class Group():
            def __init__(self, process_type, process_count, args, filename):
                self.process_type = process_type
                self.process_count = process_count
                self.args = args
                self.filename = filename
                self.memory = set()
                self.times = set()

            def __eq__(self, g):
                return self.process_type == g.process_type and \
                    self.process_count == g.process_count and \
                    self.args == g.args and \
                    self.filename == g.filename

            def get_label(self):
                return "{0}({1})\n{2}".format(self.process_type,
                                              self.process_count,
                                              self.args)

        groups = []

        for sim in self.simulations:
            f, pt, pc, a, t, m = self._get_sim_info(sim)
            group = Group(pt, pc, a, f)
            found = False
            for g in groups:
                if g == group:
                    found = True
                    g.times.add(t)
                    g.memory.add(m)
                    break
            if not found:
                group.times.add(t)
                group.memory.add(m)
                groups.append(group)

        return groups

    def _get_sim_info(self, sim):
        filename = sim.ctx.graph.filename
        process_type = sim.get_process_type()
        process_count = sim.get_process_count()
        args = sim.get_arguments()
        sim_time = sim.ctx.env.now
        memory_peak = 0
        mem_monitor = sim.ctx.monitor_manager.get_monitor("GlobalMemoryMonitor")
        if mem_monitor:
            mem_usage_entry = "memory_usage"
            data = mem_monitor.collect([mem_usage_entry])
            for _, size in data[mem_usage_entry]:
                if size > memory_peak:
                    memory_peak = size
        return filename, process_type, process_count, args, sim_time, memory_peak

    def close(self):
        for p in self.plots:
            p.dispose()
        CloseTab.close(self)


class ScalabilityTab(CloseTab):
    def __init__(self, window, process_type, arguments, model, graph):
        title = "Scalability tab - {0}".format(ntpath.basename(graph.filename))
        CloseTab.__init__(self, window, title)
        self.process_type = process_type
        self.arguments = arguments
        self.graph = graph
        self.model = model
        self.sim_worker = worker.SimWorker(self.on_start,
                                           self.on_end,
                                           self.on_error)
        self.scale_plot = None
        self.count = 0
        self.current = 0
        self.ydata = []
        self.pr_max = 32
        self.pr_step = 2
        self.pr_min = 1
        self.tick_step_val = 1

    def build(self):
        self.pb = progressbar.ProgressBar()
        self.pb.set_pulse(False)
        self.pb.connect("complete", self.on_complete)
        self.pb.start()
        for i in xrange(self.pr_min,
                        self.pr_max,
                        self.pr_step):
            sim = simulation.Simulation(self.process_type,
                                        i,
                                        self.graph,
                                        self.model,
                                        self.arguments)
            self.sim_worker.put(sim)

        self.count = self.sim_worker.q.qsize()
        self.tick_step_val = np.linspace(0, 1, self.count)
        self.sim_worker.start()
        self.vbox = gtk.VBox()
        self.vbox.pack_start(gtk.HBox())
        self.vbox.pack_start(self.pb.get_progress_bar(), False)
        self.vbox.pack_start(gtk.HBox())
        return self.vbox

    def on_start(self, sim):
        msg = "Simulating algorithm '{0}' with {1} processes\nTotal progress {2} / {3}"
        self.pb.set_progressbar_text(msg.format(self.process_type,
                                                sim.get_process_count(),
                                                self.current,
                                                self.count))

    def on_end(self, sim):
        self.current += 1
        self.ydata.append(sim.ctx.env.now)
        self.pb.set_value(self.tick_step_val[self.current - 1])
        msg = "Simulating algorithm '{0}' with {1} processes\nTotal progress {2} / {3}"
        self.pb.set_progressbar_text(msg.format(self.process_type,
                                                sim.get_process_count(),
                                                self.current,
                                                self.count))

    def on_error(self, err):
        msg = "In simulation was found error: '{0}'".format(err)
        self.pb.set_progressbar_text(msg)
        self.sim_worker.quit()
        self.pb.set_value(1)
        self.pb.stop()

    def on_complete(self):
        self.scale_plot = plot.ScalabilityPlot(self.process_type,
                                                self.pr_min,
                                                self.pr_max,
                                                self.pr_step,
                                                self.ydata)
        self.scale_plot.draw()
        self.remove(self.vbox)
        self.pack_start(self.scale_plot.get_widget_with_navbar(self.win))
        self.show_all()

    def close(self):
        self.sim_worker.quit()
        self.pb.stop()
        if self.scale_plot:
            self.scale_plot.dispose()
        CloseTab.close(self)

