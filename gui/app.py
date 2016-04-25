import paths
import sys
sys.path.append(paths.ROOT)
import window
import tab
import gtk
import gobject
from dialogs import messagedialog as msgd, multisimdialog as msimd
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

            sim_dialog = msimd.MultiSimulationDialog(self.window,
                                                     self.simulator.get_available_processor_types())
            result = sim_dialog.run()
            if result != gtk.RESPONSE_OK:
                sim_dialog.destroy()
                return

            sim_data = sim_dialog.get_data()
            sim_dialog.destroy()
            
            if sim_data[0] > 0 and len(sim_data[1]) > 0:                
                sim_progress_tab = tab.SimulationProgressTab("Simulation",
                                                             self.window,
                                                             self.project,
                                                             sim_data)
                self.window.create_tab(sim_progress_tab)

    def start_graphics_simulation(self):
        if self.project:
            graph = self.project.get_graph()
            if len(graph.nodes) < 100:
                sim_tab = self.window.create_tab(SimulationTab(self.project, self.window))
                sim_tab.start()
            else:
                msgd.MessageDialog().error_dialog(self.window,
                                                "Graph is too large for visual simulation")
            