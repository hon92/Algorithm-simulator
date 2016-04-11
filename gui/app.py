import window
import tab
import gtk
import gobject
import threading
from dialogs import simulationdialog as simd, messagedialog as msgd
from sim.simulation import Simulation
from simulationtab import SimulationTab
from dialogs.xmldialog import XMLDialog
from gui.project import Project
gobject.threads_init()

class App():
    def __init__(self):
        self.project = None
        self.window = window.Window(self)
        self.simulator = None
        self.visible_simulator = None

    def run(self):
        self.window.show()
        gtk.threads_enter()
        gtk.main()
        gtk.threads_leave()

    def close(self):
        if self.project:
            self.close_project()
        gtk.main_quit()

    def open_project(self):
        project_file = XMLDialog.open_file()
        if project_file:
            if self.project:
                self.close_project()

            try:
                project = Project(project_file)
                project.open()
                self.window.set_title(project.get_project_name())
                self.project = project
                msgd.MessageDialog().info_dialog(self.window,
                                                 "Project " + project.get_project_name_without_extension()
                                                 + " was successfully loaded")
            except Exception as ex:
                msgd.MessageDialog().error_dialog(self.window,
                                                  "Project file "+ 
                                                  project_file.get_filename() +
                                                  " is corrupted and cant be opened")

    def close_project(self):
        if self.project:
            if self.simulator:
                self.simulator.stop()
                self.simulator = None
            self.project.close()
            self.window.set_title("")
            self.project = None

    def save_project(self):
        if self.project:
            file = self.project.get_project_file()
            saved = XMLDialog.save_file(file)
            if saved:
                msgd.MessageDialog().info_dialog(self.window,
                                                 "Project " + self.project.get_project_name_without_extension()
                                                 + " was saved")
            else:
                msgd.MessageDialog().error_dialog(self.window,
                                                 "Project " + self.project.get_project_name_without_extension()
                                                 + " was not saved due to error")

    def open_settings(self):
        if self.project:
            pass

    def start_simulation(self):
        if self.project:
            if not self.simulator:
                self.simulator = Simulation(self.project.get_graph())
    
            self.simulator.stop()

            sim_dialog = simd.SimulationDialog(self.window, self.simulator.get_available_processor_types())
            result = sim_dialog.run()
            if result != gtk.RESPONSE_OK:
                sim_dialog.destroy()
                return

            process_count = sim_dialog.get_process_count()
            process_type = sim_dialog.get_process_type()
            sim_dialog.destroy()
            self.simulator.register_n_processes(process_type, process_count)

            new_thread = threading.Thread(target= lambda:self.simulator.start())
            new_thread.daemon = True
            new_thread.start()

            title = "Sim: {0}({1})".format(process_type, process_count)
            progress_tab = tab.SimProgressBarTab(title, self.simulator, self.window)
            self.window.create_tab(progress_tab)
            progress_tab.start()

    def start_graphics_simulation(self):
        if self.project:
            graph = self.project.get_graph()
            if len(graph.nodes) < 100:
                sim_tab = self.window.create_tab(SimulationTab(self.project, self.window))
                sim_tab.start()
            else:
                msgd.MessageDialog().error_dialog(self.window,
                                                "Graph is too large for visual simulation")
            