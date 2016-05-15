import paths
import sys
from gui.exceptions import ProjectException
sys.path.append(paths.ROOT)
import gtk
import window
import tab
import gobject
from dialogs import inputdialog
from dialogs.xmldialog import XMLDialog
from project import Project

gobject.threads_init()

class App():
    def __init__(self):
        self.project = None
        self.window = window.Window(self)
        self.window.create_tab(tab.WelcomeTab(self.window, "Welcome tab"))

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
        project_name = inputdialog.InputDialog("Insert project name", self.window).run()
        if project_name:
            if self.project:
                self.project.close()

            project = Project.create_empty_project(project_name)
            project.set_name(project_name)
            project.save()
            self._open_project(project)
            
            self.window.console.writeln("Project "
                                           + project.get_project_name_without_extension()
                                           + " was created")

    def open_project(self):
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