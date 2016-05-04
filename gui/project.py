import os
import graphloader
import subprocess
import paths
import projectloader as pl
from dot import DotGraphBuilder

class Project():
    def __init__(self, project_file):
        self.project_file = project_file
        self.name = ""
        self.is_open_project = False
        self.files = {} # key -> graph xml file, value -> (graph, visible_graph)
        self.project_loader = pl.ProjectLoader(project_file)
        self.opened_tabs = []

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

    def is_open(self):
        return self.is_open_project

    def open(self):
        if not self.is_open():
            project_name, files = self.project_loader.load()
            if project_name:
                self.set_name(project_name)
            for filename in files:
                self.add_graph_file(filename)
            self.is_open_project = True

    def save(self):
        return self.project_loader.save(self.name, self.files)

    def close(self):
        for t in self.opened_tabs:
            t.close()
        del self.opened_tabs
        del self.files

    def add_graph_file(self, filename):
        if filename not in self.files:
            if filename.endswith(".xml") and os.path.exists(filename):
                self.files[filename] = (None, None)
                return True
        return False

    def remove_graph_file(self, filename):
        if filename in self.files:
            del self.files[filename]

    def get_graph(self, filename):
        if not self.is_open():
            self.open()
        if filename in self.files:
            graph, visible_graph = self.files[filename]
            if not graph:
                graph = graphloader.GraphLoader(filename).load()
                self.files[filename] = (graph, visible_graph)
            return graph

    def get_visible_graph(self, filename):
        if not self.is_open():
            self.open()
        
        if filename in self.files:
            graph, visible_graph = self.files[filename]
            if not visible_graph:
                graph = self.get_graph(filename)
                dot_file = filename.replace(".xml", "") + ".dot"
                dot_builder = DotGraphBuilder(graph, dot_file)
                dot_builder.write()
                dot_app = paths.DOT_CMD_STRING
                dot_file = dot_builder.dot_file
                new_file = self.project_file + self.get_project_name_without_extension() + ".svg"
                args = dot_app +  " -Tsvg " + dot_file + " -o" + new_file
                result = subprocess.call(args, shell = True)          
                if result == 0:
                    visible_graph = graphloader.SVGVisibleGraphLoader(graph, new_file).load()
                    self.files[filename] = (graph, visible_graph)
            return visible_graph
