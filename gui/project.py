import os
import graphmanager
from gui import exceptions as exc
from gui.events import EventSource


class Project(EventSource):
    def __init__(self, filename, name):
        EventSource.__init__(self)
        self.register_event("error")
        self.filename = filename
        self.name = name
        self.saved = True
        self.opened_tabs = []
        self.graph_manager = graphmanager.GraphManager()

    def get_name(self):
        return self.name

    def get_file(self):
        return self.filename

    def add_tab(self, tab):
        self.opened_tabs.append(tab)

    def remove_tab(self, tab):
        if tab in self.opened_tabs:
            self.opened_tabs.remove(tab)

    def get_project_tab(self):
        return self.opened_tabs[0]

    def get_simulations_tab(self):
        return self.opened_tabs[1]

    def is_saved(self):
        return self.saved

    def add_file(self, filename):
        if filename in self.graph_manager.graphs:
            self.fire("error", "'{0}' is already in project".format(filename))
            return
        if not filename.endswith(".xml"):
            self.fire("error", "'{0}' is invalid graph filename".format(filename))
            return
        if not os.path.exists(filename):
            self.fire("error", "'{0}' not exists".format(filename))
            return

        try:
            self.graph_manager.register_graph(filename)
            self.saved = False
            return True
        except exc.GraphException as ex:
            self.fire("error", ex.message)

    def remove_file(self, filename):
        self.saved = False
        self.graph_manager.unregister_graph(filename)

    def get_files(self):
        return self.graph_manager.get_graph_files()

    def close(self):
        for t in reversed(self.opened_tabs):
            t.close()

