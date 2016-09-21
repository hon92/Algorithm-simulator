import graphloader
import paths
import dot
import subprocess
import os
from gui import exceptions as ex

class GraphManager():
    POOL_SIZE = 2
    def __init__(self):
        self.graphs = {}
        self.visible_graphs = {}

    def get_graph_files(self):
        return [filename for filename in self.graphs]

    def register_graph(self, filename):
        try:
            graph = self.get_graph_now(filename)
            self.graphs[filename] = [graph]
            self.visible_graphs[filename] = []
        except Exception:
            raise ex.GraphException("Graph in '{0}' is corrupted".format(filename))

    def unregister_graph(self, filename):
        if filename in self.graphs:
            del self.graphs[filename]
        if filename in self.visible_graphs:
            del self.visible_graphs[filename]

    def get_origin_graph(self, filename):
        if filename in self.graphs:
            return self.graphs[filename][0]

    """
    def get_graph(self, filename):
        print "get graph", filename
        if filename in self.graphs:
            available_graphs = self.graphs[filename]
            if len(available_graphs) > 0:
                return available_graphs.pop()
            elif len(available_graphs) == 0:
                return self.get_graph_now(filename)
    """
    def get_graph(self, filename):
        if filename in self.graphs:
            return self.graphs[filename][0]

    def get_visible_graph(self, filename):
        if filename in self.visible_graphs:
            available_visible_graphs = self.visible_graphs[filename]
            if len(available_visible_graphs) > 0:
                return available_visible_graphs.pop()
            elif len(available_visible_graphs) == 0:
                return self.get_visible_graph_now(filename)
        else:
            visible_graph = self.get_visible_graph_now(filename)
            self.visible_graphs[filename] = []
            return visible_graph

    def _make_svg_file(self, graph, filename):
        dot_file = filename.replace(".xml", "") + ".dot"
        dot_builder = dot.DotGraphBuilder(graph, dot_file)
        dot_builder.write()
        dot_app = paths.DOT_CMD_STRING
        dot_file = dot_builder.dot_file
        new_file = filename.replace(".xml", "") + ".svg"
        args = dot_app +  " -Tsvg " + dot_file + " -o" + new_file
        result = subprocess.call(args, shell = True)
        if result == 0:
            return new_file
        else:
            return None

    def get_graph_now(self, filename):
        graph = graphloader.GraphLoader(filename).load()
        graph.filename = filename
        return graph

    def get_visible_graph_now(self, filename):
        graph = self.get_graph(filename)
        svg_file = filename.replace(".xml", ".svg")

        if not os.path.exists(svg_file):
            new_file = self._make_svg_file(graph, filename)
        else:
            new_file = svg_file

        visible_graph = None
        if new_file:
            visible_graph = graphloader.SVGVisibleGraphLoader(graph, new_file).load()
            visible_graph.filename = filename
        self.return_graph(graph)
        return visible_graph

    def return_graph(self, graph, visibile_graf = False):
        filename = graph.filename
        if visibile_graf:
            current_graphs = self.visible_graphs[filename]
        else:
            current_graphs = self.graphs[filename]

        if len(current_graphs) < self.POOL_SIZE:
            if visibile_graf:
                self.visible_graphs[filename].append(graph)
            else:
                self.graphs[filename].append(graph)
