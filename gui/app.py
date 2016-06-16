import paths
import sys
sys.path.append(paths.ROOT)
import gtk
import window
import tab
import gobject
import appargs
from dialogs import inputdialog
from dialogs.xmldialog import XMLDialog
from project import Project
from gui.exceptions import ProjectException
from sim.processes import process

gobject.threads_init()
process.load()

class App():
    def __init__(self, args):
        self.project = None
        self.window = window.Window(self)
        self.window.create_tab(tab.WelcomeTab(self.window, "Welcome tab"))
        self.app_args = appargs.AppArgs(self, args)
        self.app_args.solve()

    def run(self):
        self.window.show()
        gtk.threads_enter()
        gtk.main()
        gtk.threads_leave()

    def close(self):
        if self.project:
            self.close_project()
        gtk.main_quit()

    def _open_project(self, project):
        project.open()
        self.project = project
        project_tab = tab.ProjectTab(self.window, project)
        self.window.create_tab(project_tab)
        project_tab.load()

    def create_project(self):
        project_name = XMLDialog.save_as_file()
        if project_name and project_name.endswith(".xml"):
            if self.project:
                self.project.close()

            project = Project.create_empty_project(project_name)
            project.set_name(project_name)
            project.save()
            self._open_project(project)
            self.window.console.writeln("Project was created in " + project_name)
        else:
            self.window.console.writeln("Project invalid name")

    def open_project(self, project_file = None):
        if not project_file:
            project_file = XMLDialog.open_file()

        if project_file:
            if self.project:
                self.close_project()

            try:
                project = Project(project_file)
                self._open_project(project)
                self.window.console.writeln("Project " + project.get_project_name_without_extension()
                                                 + " was successfully opened")
            except ProjectException:
                self.window.console.writeln("Project is corrupted", "err")

    def close_project(self):
        if self.project:
            self.project.close()
            self.window.set_title("")
            self.project = None
            self.window.console.writeln("Project was closed")

    def save_project(self):
        if self.project:
            saved = self.project.save()
            if saved:
                self.window.console.writeln("Project "
                                            + self.project.get_project_name_without_extension()
                                            + " was saved")
            else:
                self.window.console.writeln("Project "
                                            + self.project.get_project_name_without_extension()
                                            + " was not saved due to error", "err")

    def open_settings(self):
        if self.project:
            pass

    def start_simulation(self):
        if self.project:
            self.project.get_project_tab().run_simulations()

    def start_graphics_simulation(self):
        if self.project:
            self.project.get_project_tab().run_vizual_simulations()