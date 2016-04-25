import gtk
import paths
from misc import progressbar, timer
from sim import plot, simulation
from dialogs import csvdialog as csvd, messagedialog as msgd
import statisticsdata
import threading

class Tab(gtk.VBox):
    def __init__(self, title):
        gtk.VBox.__init__(self)
        self.show()
        self.title_text = title
        self.notebook = None

    def set_title(self, title):
        self.title_text = title

    def get_title(self):
        return self.title_text

    def get_tab_label(self):
        return gtk.Label(self.title_text)

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
        hbox = gtk.HBox(False, 0)
        hbox.pack_start(gtk.Label(self.title_text))
        hbox.pack_start(self.close_button, False, False)
        hbox.show_all()
        return hbox

    def on_close(self, w, tab):
        if self.notebook:
            page_number = self.notebook.page_num(tab)
            self.notebook.remove_page(page_number)

    def close(self):
        self.on_close(self, self)

class WelcomeTab(CloseTab):
    def __init__(self, title):
        CloseTab.__init__(self, title)
        self.pack_start(gtk.Label("Welcome in simulator"))

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

class PlotTab(CloseTab):
    def __init__(self, title, simulator):
        CloseTab.__init__(self, title)
        self.widget = plot.SimPlotWidget(simulator)
        self.pack_start(self.widget)

    def on_close(self, w, tab):
        self.widget.close()
        CloseTab.on_close(self, w, tab)


class SimulationProgressTab(CloseTab):
    def __init__(self, title, window, project, sim_properties):
        CloseTab.__init__(self, title)
        self.liststore = gtk.ListStore(str, int, str, float) # process type, progress, status, time
        self.simulators = []
        self.current_iter = -1
        self.win = window
        self.timer = timer.Timer(1000, self.on_timeout)
        self._prepare_data(sim_properties, project)
        self._create_content()
        self.start_next_sim()

    def _prepare_data(self, sim_properties, project):
        sim_count = sim_properties[0]

        for i in xrange(sim_count):
            for process_type, process_count in sim_properties[1]:
                simulator = simulation.Simulation(project.get_graph())
                simulator.register_n_processes(process_type, process_count)
                process_info = "{0}({1})".format(process_type, process_count)
                self.liststore.append([process_info, 0, "PENDING", 0.0])
                self.simulators.append(simulator)

    def _create_content(self):
        export_image = gtk.Image()
        icons_path = paths.ICONS_PATH
        export_image.set_from_file(icons_path + "CSV-24.png")
        
        cancel_image = gtk.Image()
        cancel_image.set_from_file(icons_path + "Close Window-24.png")

        show_image = gtk.Image()
        show_image.set_from_file(icons_path + "Show Property-24.png")

        self.export_button = gtk.Button()
        self.export_button.add(export_image)
        self.export_button.set_tooltip_text("Export data to CSV")
        self.export_button.connect("clicked", self.on_export)
        self.export_button.show_all()

        self.cancel_button = gtk.Button()
        self.cancel_button.add(cancel_image)
        self.cancel_button.set_tooltip_text("Cancel simulation")
        self.cancel_button.connect("clicked", self.on_cancel)
        self.cancel_button.show_all()
        
        self.show_button = gtk.Button()
        self.show_button.add(show_image)
        self.show_button.set_tooltip_text("Show results")
        self.show_button.connect("clicked", self.on_show_results)
        self.show_button.show_all()

        self.treeview = self._create_tree_view()
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add_with_viewport(self.treeview)
        self.pack_start(sw)
        hbox = gtk.HBox()
        hbox.pack_start(self.show_button)
        hbox.pack_start(self.export_button)
        hbox.pack_start(self.cancel_button)
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
        if self.current_iter + 1 < len(self.simulators):
            self.current_iter += 1
            self.liststore[self.current_iter][2] = "In progress"
            self.timer.start()            
            sim = self.simulators[self.current_iter]
            sim.connect("end_simulation", lambda s: self.on_sim_complete(s, self.current_iter))
            new_thread = threading.Thread(target = lambda: sim.start())
            new_thread.daemon = True
            new_thread.start()

    def on_timeout(self):
        sim = self.simulators[self.current_iter]
        values = sim.graph.nodes.values()
        nodes_count = len(values)
        curr_count = 0
        for node in values:
            if node.is_discovered():
                curr_count += 1

        new_val = curr_count / float(nodes_count)
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

    def on_cancel(self, w):
        index = self.get_selected_row_index()
        if index > -1:
            sim = self.simulators[index]
            if sim.is_running():
                sim.stop()

    def on_export(self, w):
        index = self.get_selected_row_index()
        if index > -1:
            if self.liststore[index][2] == "Completed":
                sim = self.simulators[index]
                if not sim.is_running():
                    new_file = csvd.CSVDialog.save_as_file()
                    if new_file:
                        if not new_file.get_path().endswith(".csv"):
                            msgd.MessageDialog().error_dialog(self.win,
                                "File name has to end with .csv")
                            return
                        ex = statisticsdata.CSVExportDataModule(sim)
                        ex.print_to_file(new_file)
                        msgd.MessageDialog().info_dialog(self.win,
                                "Data was successfully exported to " + new_file.get_path())

    def on_show_results(self, w):
        index = self.get_selected_row_index()
        if index > -1:
            if self.liststore[index][2] == "Completed":
                sim = self.simulators[index]
                self.win.create_tab(PlotTab(self.liststore[index][0] + "- Detail", sim))

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
        for sim in self.simulators:
            if sim.is_running():
                sim.stop()
        CloseTab.on_close(self, w, tab)
