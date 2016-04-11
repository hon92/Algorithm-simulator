from dot import DotGraphBuilder
import graphloader
import subprocess
import sys

class Project():
    def __init__(self, project_file):
        self.project_file = project_file
        self.graph = None
        self.name = ""
        self.visible_graph = None
        self.tabs = []

    def set_name(self, name):
        self.name = name

    def get_project_name(self):
        if not self.name:
            filename = self.project_file.get_basename()
            return filename
        return self.name

    def get_project_name_without_extension(self):
        full_filename = self.get_project_name()
        return full_filename.replace(".xml", "")

    def is_opened(self):
        return self.graph is not None

    def open(self):
        if not self.is_opened():
            self.graph = graphloader.ProjectLoader(self.get_project_file_path()).load()

    def close(self):
        for t in self.tabs:
            t.close()

    def get_project_file_path(self):
        return self.project_file.get_path()

    def get_project_path(self):
        full_path = self.get_project_file_path()
        filename = self.get_project_name()
        return full_path[:(len(full_path) - len(filename))]

    def get_graph(self):
        if not self.is_opened():
            self.open()
        return self.graph

    def get_visible_graph(self):
        if not self.visible_graph:
            dot_builder = DotGraphBuilder(self)
            dot_builder.write()
            dot_path = "C:\\Program Files (x86)\\Graphviz2.38\\bin\\"
            dot_program = "dot.exe"
            if sys.platform == "win32":
                dot_app = '\"' + dot_path + dot_program + '\"'
            else:
                dot_app = "dot"

            dot_file = dot_builder.dot_file
            new_file = self.get_project_path() + self.get_project_name_without_extension() + ".svg"
            args = dot_app +  " -Tsvg " + dot_file + " -o" + new_file
            result = subprocess.call(args, shell = True)          
            if result == 0:
                self.visible_graph = graphloader.SVGVisibleGraphLoader(self.get_graph(), new_file).load()
        return self.visible_graph