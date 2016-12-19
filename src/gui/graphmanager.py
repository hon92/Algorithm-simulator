import graphloader
import paths
import dot
import subprocess
import os
import collections
from gui import exceptions as ex


class GraphManager():
    def __init__(self):
        self.graphs = collections.OrderedDict()
        self.visible_graphs = {}

    def add_graph_file(self, filename):
        try:
            graph = self._load_graph(filename)
            self.graphs[filename] = graph
            self.visible_graphs[filename] = None
        except Exception:
            raise ex.GraphException("Graph in '{0}' is corrupted".format(filename))

    def remove_graph_file(self, filename):
        if filename in self.graphs:
            del self.graphs[filename]
        if filename in self.visible_graphs:
            del self.visible_graphs[filename]

    def contain_filename(self, filename):
        return self.graphs.get(filename) != None

    def get_graph_files(self):
        return self.graphs.keys()

    def get_graph(self, filename):
        return self.graphs.get(filename)

    def get_visual_graph(self, filename):
        vis_graph = self.visible_graphs.get(filename)
        if not vis_graph:
            graph = self.get_graph(filename)
            vis_graph = self._load_visual_graph(graph, filename)
            self.visible_graphs[filename] = vis_graph
        return vis_graph

    def _load_graph(self, filename):
        graph = graphloader.GraphLoader(filename).load()
        graph.filename = filename
        return graph

    def _load_visual_graph(self, graph, filename):
        graph = self.get_graph(filename)
        svg_file = filename.replace(".xml", ".svg")

        if not os.path.exists(svg_file):
            svg_file = self._create_svg_file(graph, filename)

        visible_graph = None
        if svg_file:
            visible_graph = graphloader.SVGVisibleGraphLoader(graph, svg_file).load()
            visible_graph.filename = filename
        return visible_graph

    def _create_svg_file(self, graph, filename):
        dot_file = filename.replace(".xml", ".dot")
        dot_builder = dot.DotGraphBuilder(graph, dot_file)
        dot_builder.write()
        dot_app = paths.DOT_CMD_STRING
        new_svg_file = filename.replace(".xml", ".svg")
        args = dot_app + " -Tsvg " + dot_file + " -o " + new_svg_file
        result = subprocess.call(args, shell = True)
        if result == 0:
            return new_svg_file
        else:
            return None

