import xml.etree.cElementTree as ET
import graph as g
from xml.etree.ElementTree import QName
from exceptions import GraphException, VisibleGraphException


class AbstractGraphLoader():
    def __init__(self, filename):
        self.tree = ET.parse(filename);
        self.root_el = self.tree.getroot()
        self.graph = None

    def solve_graph(self):
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
        self.graph = g.Graph()
        self.edges = []

    def load(self):
        try:
            self.solve_graph()
            return self.graph
        except Exception as ex:
            raise GraphException(ex.message)

    def solve_graph(self):
        self.root_node_id = self.root_el.get("init-node-id")
        nodes = self.root_el.findall("node")

        for node in nodes:
            self.solve_node(node)

        self.graph.set_root_node(self.root_node_id)
        for source_node_id, edge_el in self.edges:
            self.solve_edge(source_node_id, edge_el)

    def solve_node(self, node):
        node_id = node.get("id")
        size = float(node.get("size"))
        edges_elements = node.findall("arc")

        for edge_el in edges_elements:
            self.edges.append((node_id, edge_el))

        self.graph.add_node(g.Node(node_id, size))

    def solve_edge(self, source_node_id, edge_el):
        target_node_id = edge_el.get("node-id")
        label = edge_el.get("label")
        events_count = int(edge_el.get("events-count"))
        time = float(edge_el.get("time"))
        pids = edge_el.get("pids").split(",")
        source_node = self.graph.get_node(source_node_id)
        target_node = self.graph.get_node(target_node_id)
        self.graph.add_edge(g.Edge(source_node, target_node, time, events_count, pids, label))


class SVGVisibleGraphLoader(AbstractGraphLoader):
    def __init__(self, graph, filename):
        AbstractGraphLoader.__init__(self, filename)
        self.graph_model = graph
        self.used_edges = []

    def ls(self, text):
        return str(QName("http://www.w3.org/2000/svg", text))

    def load(self):
        try:
            root = self.root_el
            width = root.get("width")
            height = root.get("height")
            viewbox = root.get("viewBox")
            viewbox = viewbox.split(" ")
            width = int(width[:-2])
            height = int(height[:-2])
            self.graph = g.VisibleGraph(1, width, height)
            graph_item = root.find(self.ls("g"))
            self.solve_graph(graph_item)
            return self.graph
        except Exception as ex:
            raise VisibleGraphException(ex.message)

    def solve_graph(self, graph):
        polygon = graph.find(self.ls("polygon"))
        transform = graph.get("transform")
        tr = transform.split("translate", 1)[1]
        tr = tr[1:]
        tr = tr[:-1]
        tr_coords = tr.split(" ")

        self.tr_x = float(tr_coords[0])
        self.tr_y = float(tr_coords[1])
        self.graph.translate_x = self.tr_x
        self.graph.translate_y = self.tr_y

        nodes_items = graph.findall(self.ls("g[@class='node']"))
        edges_items = graph.findall(self.ls("g[@class='edge']"))

        for node in nodes_items:
            self.solve_node(node)
        for edge in edges_items:
            self.solve_edge(edge)

        for node in self.graph.nodes.values():
            edges = node.get_edges()
            sorted_edges = []
            if len(edges) == 0:
                continue
            model_edges = self.graph_model.get_node(node.get_id()).get_edges()

            for model_edge in model_edges:
                fe = [e for e in edges if e.get_time() == model_edge.get_time() and e.label == model_edge.label]

                if len(fe) > 0:
                    sorted_edges.append(fe[0])
                    edges.remove(fe[0])

            node.edges = sorted_edges

        self.graph.set_root_node(self.graph_model.root.id)

    def solve_node(self, node):
        title = node.find(self.ls("title"))
        model_node = self.graph_model.get_node(title.text)
        polygon = node.find(self.ls("polygon"))
        text = node.find(self.ls("text"))
        polygon = self.solve_polygon(polygon)
        x = polygon[2][0][0]
        y = polygon[2][0][1]
        w = polygon[2][1][0] - polygon[2][0][0]
        h = polygon[2][2][1] - polygon[2][1][1]
        x += w
        w = abs(w)
        node = g.VisibleNode(title.text, model_node.get_size(), x, y, w, h)
        self.graph.add_node(node)
        return node

    def solve_edge(self, edge):
        path = edge.find(self.ls("path"))
        polygon = edge.find(self.ls("polygon"))
        text = edge.find(self.ls("text"))
        title = edge.find(self.ls("title"))
        title = title.text.split("->")
        path = self.solve_path(path)
        polygon = self.solve_polygon(polygon)
        label = self.solve_text(text)

        target_node = self.graph.get_node(title[1])
        source_node = self.graph_model.get_node(title[0])

        model_edge = None
        source_edges = source_node.get_edges()
        for se in source_edges:
            if se.target.id == title[1] and se.label == label[2]:
                model_edge = se
                break
        if not model_edge:
            raise Exception("Model edge not found")

        edge = g.VisibleEdge(source_node,
                             target_node,
                             model_edge.get_time(),
                             model_edge.events_count,
                             model_edge.pids,
                             label[2], label[0], label[1], path[2], polygon[2])
        self.graph.add_edge(edge)
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

