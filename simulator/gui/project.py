import os
import graphmanager
import exceptions as exc


class Project():
    def __init__(self, filename, name):
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
        if self.graph_manager.contain_filename(filename):
            raise exc.GraphException("'{0}' is already in project".format(filename))
        if not filename.endswith(".xml"):
            raise exc.GraphException("'{0}' is invalid graph filename".format(filename))
        if not os.path.exists(filename):
            raise exc.GraphException ("'{0}' not exists".format(filename))

        try:
            self.graph_manager.add_graph_file(filename)
            self.saved = False
        except exc.GraphException as ex:
            raise ex

    def remove_file(self, filename):
        self.saved = False
        self.graph_manager.remove_graph_file(filename)

    def get_files(self):
        return self.graph_manager.get_graph_files()

    def close(self):
        for t in reversed(self.opened_tabs):
            t.close()

