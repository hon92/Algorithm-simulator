import paths
import sys
sys.path.insert(0, paths.SRC_PATH)
import gobject
import gtk
import window
import tab
import appargs
import operations
from gui.dialogs import dialog
from gui.projectloader import ProjectLoader

gobject.threads_init()


class App():
    def __init__(self, args):
        self.project = None
        self.window = window.Window(self)
        self.app_args = appargs.AppArgs(self, args)
        self.app_args.solve()
        self.window.create_tab(tab.WelcomeTab(self.window, "Welcome tab"))

    def run(self):
        self.window.show()
        gtk.threads_enter()
        gtk.main()
        gtk.threads_leave()

    def create_project(self):
        input_dialog = dialog.InputDialog("Insert project name", self.window)
        project_name = input_dialog.run()
        if project_name:
            project_file = dialog.Dialog.get_factory("xml").save_as("Save project file",
                                                                    text = project_name + ".xml")
            if project_file:
                if self.project:
                    self.project.close()

                try:
                    project = ProjectLoader.create_empty_project(project_file, project_name)
                    self._open_project(project)
                    msg = "Project '{0}' was created at location '{1}'"
                    self.window.console.writeln(msg.format(project.get_name(),
                                                           project.get_file()))
                except Exception as ex:
                    self.window.console.writeln(ex.message, "err")

    def open_project(self, project_file = None):
        if not project_file:
            project_file = dialog.Dialog.get_factory("xml").open("Open project")

        if project_file:
            if self.project:
                self.close_project()

            try:
                msg = "Opening project at location '{0}'".format(project_file)
                self.window.console.writeln(msg)
                project = ProjectLoader.load_project(project_file)
                self._open_project(project)
                msg = "Project '{0}' was opened".format(project.get_name())
                self.window.console.writeln(msg)
            except IOError as ex:
                raise Exception("Project file error: {0}".format(ex))
            except Exception as ex:
                self.window.console.writeln("Project is corrupted ({0})".format(ex.message), "err")

    def _open_project(self, project):
        self.project = project
        self.project.saved = True
        project_tab = tab.ProjectTab(self.window, project)
        simulations_tab = tab.SimulationsTab(self.window, project)
        self.window.create_tab(project_tab)
        self.window.create_tab(simulations_tab)

    def save_project(self):
        if self.project:
            try:
                ProjectLoader.save_project(self.project)
                self.project.saved = True
                msg = "Project '{0}' was saved".format(self.project.get_name())
                self.window.console.writeln(msg)
            except Exception as ex:
                msg = "Project '{0}' was not saved due to error({1})"
                self.window.console.writeln(msg.format(self.project.get_name(),
                                                       ex.message), "err")

    def close_project(self):
        if self.project:
            if not self.project.is_saved():
                print "you should save your project before closing"
            name = self.project.get_name()
            self.project.close()
            self.window.set_title("")
            self.project = None
            msg = "Project '{0}' was closed".format(name)
            self.window.console.writeln(msg)

    def open_settings(self):
        settings_tab = self.window.get_tab("Settings")
        if settings_tab:
            self.window.switch_to_tab(settings_tab)
        else:
            settings_tab = tab.SettingsTab(self.window)
            self.window.create_tab(settings_tab)

    def start_simulation(self):
        if self.project:
            self.project.get_project_tab().on_sim_button_clicked(None)

    def start_graphics_simulation(self):
        if self.project:
            self.project.get_project_tab().on_viz_sim_button_clicked(None)

    def generate_graph(self):
        if not self.project:
            return
        operations.GenerateGraph(self).perform()

    def generate_scalability_graph(self):
        if not self.project:
            return
        operations.ScalabilityDialog(self).perform()

    def close(self):
        if self.project:
            self.close_project()
        gtk.main_quit()

