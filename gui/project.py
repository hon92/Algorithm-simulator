import projectloader as pl
import graphmanager
from gui import exceptions as exc
from gui.events import EventSource

class Project(EventSource):
    def __init__(self, project_file):
        EventSource.__init__(self)
        self.register_event("error")
        self.project_file = project_file
        self.name = ""
        self.opened_tabs = []
        self.project_loader = pl.ProjectLoader(project_file)
        self.graph_manager = graphmanager.GraphManager()

    @staticmethod
    def create_empty_project(filename):
        return Project(filename)

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def get_file(self):
        return self.project_file

    def add_tab(self, tab):
        self.opened_tabs.append(tab)

    def remove_tab(self, tab):
        if tab in self.opened_tabs:
            self.opened_tabs.remove(tab)

    def get_tab(self):
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
                raise exc.ProjectException("Project file is corrupted")
            if project_name:
                self.set_name(project_name)
            for filename in files:
                try:
                    self.graph_manager.register_graph(filename)
                except Exception as ex:
                    self.fire("error", "Graph open error: " + ex.message)

    def save(self):
        return self.project_loader.save(self.name, self.get_files())

    def close(self):
        for t in reversed(self.opened_tabs):
            t.close()

    def load_graph_file(self, filename):
        if filename in self.graph_manager.graphs:
            raise exc.ExistingGraphException("'{0}' is already in project".format(filename))
        self.graph_manager.register_graph(filename)

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
