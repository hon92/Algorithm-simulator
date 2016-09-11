import xml.etree.cElementTree as ET
from xml.etree.ElementTree import QName
from gui import graph as g
from gui.exceptions import GraphException, VisibleGraphException

class AbstractGraphLoader():
    def __init__(self, filename):
        self.filename = filename
        self.tree = ET.parse(filename);
        self.root = self.tree.getroot()
        self.graph = None

    def get_root(self):
        return self.root

    def solve_graph(self, graph):
        pass
    
    def solve_node(self, node):
        pass

    def solve_edge(self, edge):
        pass

    def load(self):
        return self.graph


class GraphLoader(AbstractGraphLoader):
    def __init__(self, filename):
        AbstractGraphLoader.__init__(self, filename)
        self.root_node_id = self.root.get("init-node-id")
        self.graph = g.Graph()
        self.arcs = []

    def load(self):
        try:
            self.solve_graph(self.root)
            return self.graph
        except Exception as ex:
            raise GraphException(ex.message)

    def solve_graph(self, graph):
        nodes = graph.findall("node")

        for node in nodes:
            self.solve_node(node)

        self.graph.set_root_node(self.root_node_id)
        for from_node, arc in self.arcs:
            self.graph.add_edge(from_node, self.solve_edge(arc))

    def solve_node(self, node):
        arcs = node.findall("arc")
        node_id = node.get("id")
        size = float(node.get("size"))
        for arc in arcs:
            self._solve_edge(node_id, arc)

        n = g.Node(node_id, size)
        n.graph = self.graph
        self.graph.add_node(n)

    def _solve_edge(self, from_node, arc):
        self.arcs.append((from_node, arc))

    def solve_edge(self, edge):
        to_node = edge.get("node-id")
        label = edge.get("label")
        events_count = int(edge.get("events-count"))
        time = float(edge.get("time"))
        pids = edge.get("pids").split(",")
        n = self.graph.get_node(to_node)
        return g.Edge(n, time, events_count, pids, label)


class SVGVisibleGraphLoader(AbstractGraphLoader):
    def __init__(self, graph, filename):
        AbstractGraphLoader.__init__(self, filename)
        self.graph_model = graph
        self.used_edges = []

    def s(self, text):
        return str(QName("http://www.w3.org/2000/svg", text))

    def load(self):
        try:
            root = self.get_root()
            width = root.get("width")
            height = root.get("height")
            viewbox = root.get("viewBox")
            viewbox = viewbox.split(" ")
            width = int(width[:-2])
            height = int(height[:-2])
            self.graph = g.VisibleGraph(1, width, height)
            graph_item = root.find(self.s("g"))
            self.solve_graph(graph_item)
            return self.graph
        except Exception as ex:
            raise VisibleGraphException(ex.message)

    def solve_graph(self, graph):
        polygon = graph.find(self.s("polygon"))
        transform = graph.get("transform")
        tr = transform.split("translate", 1)[1]
        tr = tr[1:]
        tr = tr[:-1]
        tr_coords = tr.split(" ")

        self.tr_x = float(tr_coords[0])
        self.tr_y = float(tr_coords[1])
        self.graph.translate_x = self.tr_x
        self.graph.translate_y = self.tr_y
        self.solve_polygon(polygon)

        nodes_items = graph.findall(self.s("g[@class='node']"))
        edges_items = graph.findall(self.s("g[@class='edge']"))

        for node in nodes_items:
            self.solve_node(node)
        for edge in edges_items:
            self.solve_edge(edge)

        for node in self.graph.nodes.values():
            edges = node.get_edges()
            sorted_edges = []
            if len(edges) == 0:
                continue
            model_edges = self.graph_model.get_node(node.get_name()).get_edges()

            for model_edge in model_edges:
                fe = [e for e in edges if e.time == model_edge.get_time() and e.label == model_edge.get_label()]

                if len(fe) > 0:
                    sorted_edges.append(fe[0])
                    edges.remove(fe[0])

            node.edges = sorted_edges

        self.graph.set_root_node(self.graph_model.root.name)

    def solve_node(self, node):
        title = node.find(self.s("title"))
        model_node = self.graph_model.get_node(title.text)
        polygon = node.find(self.s("polygon"))
        text = node.find(self.s("text"))
        polygon = self.solve_polygon(polygon)
        x = polygon[2][0][0]
        y = polygon[2][0][1]
        w = polygon[2][1][0] - polygon[2][0][0]
        h = polygon[2][2][1] - polygon[2][1][1]
        x += w
        w = abs(w)
        node = g.VisibleNode(title.text, model_node.get_size(), x, y, w, h)
        node.graph = self.graph
        self.graph.add_node(node)
        return node

    def solve_edge(self, edge):
        path = edge.find(self.s("path"))
        polygon = edge.find(self.s("polygon"))
        text = edge.find(self.s("text"))
        title = edge.find(self.s("title"))
        title = title.text.split("->")
        source = title[0]
        destination = title[1]
        path = self.solve_path(path)
        polygon = self.solve_polygon(polygon)
        label = self.solve_text(text)
        destination_node = self.graph.get_node(destination)
        source_node = self.graph_model.get_node(source)
        sources_edges = [e for e in source_node.get_edges() 
                         if e.destination.name == destination and e.label == label[2]]
        model_edge = sources_edges[0]
        edge = g.VisibleEdge(destination_node, model_edge.get_time(),
                             model_edge.events_count, model_edge.pids,
                             label[2], label[0], label[1], path[2], polygon[2])
        self.graph.add_edge(source, edge)
        return edge

    def solve_polygon(self, polygon):
        fill = polygon.get("fill")
        stroke = polygon.get("stroke")
        points = polygon.get("points")
        points = points.split(" ")
        coordinates = []
        for point in points:
            coord = point.split(",")
            x = float(coord[0]) + self.tr_x
            y = float(coord[1]) + self.tr_y
            coordinates.append((x, y))
        return (fill, stroke, coordinates)
    
    def solve_text(self, text):
        x = text.get("x")
        y = text.get("y")
        font_size = text.get("font-size")
        value = text.text
        return (float(x) - self.tr_x - 4.5, float(y) + self.tr_y, value, font_size)

    def solve_path(self, path):
        fill = path.get("fill")
        stroke = path.get("stroke")
        d = path.get("d").replace("C", " ").replace("M", "")
        coordinates = []
        for point in d.split(" "):
            coord = point.split(",")
            x = float(coord[0]) + self.tr_x
            y = float(coord[1]) + self.tr_y
            coordinates.append((x, y))
        return (fill, stroke, coordinates)

