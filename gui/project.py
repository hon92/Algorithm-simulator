import paths
import projectloader as pl
import graphmanager
from gui.exceptions import ProjectException

class Project():
    def __init__(self, project_file):
        self.project_file = project_file
        self.name = ""
        self.project_loader = pl.ProjectLoader(project_file)
        self.opened_tabs = []
        self.graph_manager = graphmanager.GraphManager()

    @staticmethod
    def create_empty_project(name):
        new_file = paths.ROOT + "\\" + name + ".xml"
        return Project(new_file)

    def set_name(self, name):
        self.name = name

    def get_project_name(self):
        if not self.name:
            return self.project_file
        return self.name

    def get_project_name_without_extension(self):
        full_filename = self.get_project_name()
        return full_filename.replace(".xml", "")

    def get_project_file(self):
        return self.project_file

    def add_tab(self, tab):
        self.opened_tabs.append(tab)

    def remove_tab(self, tab):
        if tab in self.opened_tabs:
            self.opened_tabs.remove(tab)

    def get_project_tab(self):
        if self.is_open():
            return self.opened_tabs[0]
        return None

    def is_open(self):
        return len(self.opened_tabs) != 0

    def open(self):
        if not self.is_open():
            try:
                project_name, files = self.project_loader.load()
            except Exception as ex:
                raise ProjectException(ex.message)
            if project_name:
                self.set_name(project_name)
            for filename in files:
                self.add_graph_file(filename)

    def save(self):
        return self.project_loader.save(self.name, self.get_files())

    def close(self):
        for t in reversed(self.opened_tabs):
            t.close()
        files = self.get_files()
        for filename in files:
            self.graph_manager.unregister_graph(filename)

    def add_graph_file(self, filename):
        return self.graph_manager.register_graph(filename)

    def remove_graph_file(self, filename):
        self.graph_manager.unregister_graph(filename)

    def get_graph(self, filename):
        if not self.is_open():
            self.open()
        return self.graph_manager.get_graph(filename)

    def get_visible_graph(self, filename):
        if not self.is_open():
            self.open()
        return self.graph_manager.get_visible_graph(filename)

    def get_files(self):
        return self.graph_manager.get_graph_files()
