import os
import itertools
from random import Random
from gui.graph import Edge, Node, Graph
from xml.etree.cElementTree import Element, SubElement
from misc import utils


class GraphGenerator():
    CHARACTERS = ["a","b", "c", "d", "e", "f", "g", "h", "i", "j"]
    NAME_LEN = 10

    def __init__(self, filename, nodes_count, edges_count, properties, seed = -1):
        self.filename = filename
        self.nodes_count = nodes_count
        self.edges_count = edges_count
        self.properties = properties
        self.r = Random() if seed != -1 else Random(seed)
        self.name_generator = self.create_name_generator()

        if filename == "":
            raise Exception("Filename is empty")

        if not filename.endswith(".xml"):
            raise Exception("Filename should end with '.xml'")

        if os.path.exists(filename):
            raise Exception(filename + " already exists")

        self.filename = os.path.abspath(filename)

    def create_name_generator(self):
        perm_gen = itertools.permutations(self.CHARACTERS, self.NAME_LEN)

        while True:
            try:
                next_perm = next(perm_gen)
                yield "".join(next_perm)
            except StopIteration:
                break

    def next_name(self):
        try:
            return next(self.name_generator)
        except StopIteration:
            return None

    def generate_graph(self):
        graph = Graph()
        root_node = Node("init", self.next_node_size())

        nodes = []
        nodes.append(root_node)
        for _ in xrange(self.nodes_count):
            name = self.next_name()
            n = Node(name, self.next_node_size())
            nodes.append(n)

        for _ in xrange(self.edges_count):
            source_n = nodes[self.r.randint(0, len(nodes) - 1)]
            dest_n = nodes[self.r.randint(0, len(nodes) - 1)]
            time = self.r.random()
            events_count = self.r.randint(1, 1000)
            pids = ""
            label = source_n.get_id() + "/" + dest_n.get_id()
            e = Edge(dest_n, time, events_count, pids, label)
            source_n.add_edge(e)

        for n in nodes:
            graph.add_node(n)

        graph.set_root_node("init")
        return graph

    def next_node_size(self):
        return self.r.randint(0, 10)

    def create_graph(self):
        graph = self.generate_graph()
        self.save_graph(self.filename, graph)
        return self.filename

    def save_graph(self, filename, graph):
        root = Element("statespace")
        root.set("init-node-id", graph.get_root().get_id())

        def save_node(node):
            node_el = SubElement(root, "node")
            node_el.set("id", str(node.get_id()))
            node_el.set("size", str(node.get_size()))
            return node_el

        def save_edge(edge, parent_node_el):
            edge_el = SubElement(parent_node_el, "arc")
            edge_el.set("node-id", edge.get_target().get_id())
            edge_el.set("label", edge.get_label())
            edge_el.set("events-count", str(edge.get_events_count()))
            edge_el.set("time", str(edge.get_time()))
            edge_el.set("pids", str(edge.get_pids()))
            return edge_el

        for n in graph.nodes.values():
            n_el = save_node(n)
            for e in n.get_edges():
                save_edge(e, n_el)

        with open(self.filename, "w") as f:
            f.write(utils.get_pretty_xml(root))
            f.flush()

