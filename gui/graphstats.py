from misc import utils, colors


class GraphStats():
    def __init__(self, graph):
        self.nodes_count = graph.get_nodes_count()
        self.edges_count = graph.get_edges_count()
        self.undiscovered_nodes_count = self.nodes_count
        self.undiscovered_edges_count = self.edges_count
        self.nodes_discoverers = {}
        self.edges_discoverers = {}
        self.edges_calculators = {}

    def discover_node(self, node_id, process_id):
        self.nodes_discoverers[node_id] = process_id
        self.undiscovered_nodes_count -= 1

    def discover_edge(self, source_node_id, target_node_id, label, process_id):
        self.edges_discoverers[(source_node_id, target_node_id, label)] = process_id
        self.undiscovered_edges_count -= 1

    def calculate_edge(self, source_node_id, target_node_id, label, process_id):
        self.edges_calculators[(source_node_id, target_node_id, label)] = process_id

    def is_node_discovered(self, node_id):
        return node_id in self.nodes_discoverers

    def is_edge_discovered(self, source_node_id, target_node_id, label):
        return (source_node_id, target_node_id, label) in self.edges_discoverers

    def is_edge_completed(self, source_node_id, target_node_id, label):
        return (source_node_id, target_node_id, label) in self.edges_calculators

    def get_node_discoverer(self, node_id):
        if node_id in self.nodes_discoverers:
            return self.nodes_discoverers[node_id]
        return None

    def get_edge_discoverer(self, source_node_id, target_node_id, label):
        if (source_node_id, target_node_id, label) in self.edges_discoverers:
            return self.edges_discoverers[(source_node_id, target_node_id, label)]
        return None

    def get_edge_completer(self, source_node_id, target_node_id, label):
        if (source_node_id, target_node_id, label) in self.edges_calculators:
            return self.edges_calculators[(source_node_id, target_node_id, label)]
        return None

    def reset(self):
        self.undiscovered_nodes_count = self.nodes_count
        self.undiscovered_edges_count = self.edges_count
        self.nodes_discoverers = {}
        self.edges_calculators = {}
        self.edges_discoverers = {}

    def get_nodes_count(self):
        return self.nodes_count

    def get_edges_count(self):
        return self.edges_count

    def get_undiscovered_nodes_count(self):
        return self.undiscovered_nodes_count

    def get_undiscovered_edges_count(self):
        return self.undiscovered_edges_count

    def get_discovered_nodes_count(self):
        return self.nodes_count - self.undiscovered_nodes_count

    def get_discovered_nodes_by_process(self, process_id):
        return self._count_by_process_id(process_id, self.nodes_discoverers)

    def get_discovered_edges_by_process(self, process_id):
        return self._count_by_process_id(process_id, self.edges_discoverers)

    def get_calculated_edges_by_process(self, process_id):
        return self._count_by_process_id(process_id, self.edges_calculators)

    def _count_by_process_id(self, process_id, dictionary):
        c = 0
        for _, v in dictionary.iteritems():
            if v == process_id:
                c += 1
        return c


class VisualGraphStats(GraphStats):

    #DEFAULT_NODE_COLOR = (155, 155, 155)
    VISIBLE_NODE_COLOR = (160, 220, 123)
    UNVISIBLE_NODE_COLOR = (155, 155, 155)
    SELECTED_NODE_COLOR = (99, 99, 99)

    ARROW_COLOR = (255, 255, 255)
    UNVISIBLE_EDGE_COLOR = (155, 155, 155)
    VISIBLE_EDGE_COLOR = (160, 220, 123)

    def __init__(self, graph, colors_count):
        GraphStats.__init__(self, graph)
        self.visible_nodes = {} #key-> discoverer, value -> node id
        self.visible_edges = {}
        self.colors_count = colors_count
        self.colors = []
        self.selected_node_id = None
        self._set_colors()

    def _set_colors(self):
        self.colors = []
        cc = colors.new_color_cycler()
        for _ in xrange(self.colors_count):
            self.colors.append(utils.hex_to_rgb(next(cc)))

    def set_selected_node(self, node_id):
        self.selected_node_id = node_id

    def set_node_visibility(self, node_id, val):
        pass

    def set_edge_visibility(self, source_node_id, target_node_id, label, val):
        if val:
            if not (source_node_id, target_node_id, label) in self.visible_edges:
                self.visible_edges[(source_node_id, target_node_id, label)] = True
        else:
            if (source_node_id, target_node_id, label) in self.visible_edges:
                del self.visible_edges[(source_node_id, target_node_id, label)]

    def reset(self):
        GraphStats.reset(self)
        self._set_colors()
        print "graph colors reset"

    def is_node_visible(self, node_id):
        return node_id in self.visible_nodes

    def is_edge_visible(self, source_node_id, target_node_id, label):
        return (source_node_id, target_node_id, label) in self.visible_edges

    def is_selected_node(self, node_id):
        return self.selected_node_id and self.selected_node_id == node_id

    def get_node_color(self, node_id):
        discoverer = self.get_node_discoverer(node_id)
        if discoverer is not None:
            return self.colors[discoverer]

        if self.is_node_visible(node_id):
            return self.VISIBLE_NODE_COLOR
        else:
            return self.UNVISIBLE_NODE_COLOR

    def get_inverted_color(self, color):
        return utils.get_inverted_color(color)

    def get_edge_color(self, source_node_id, target_node_id, label):
        completer = self.get_edge_completer(source_node_id, target_node_id, label)
        if completer is not None:
            return self.colors[completer]
        discoverer = self.get_edge_discoverer(source_node_id, target_node_id, label)
        if discoverer is not None:
            return self.colors[discoverer]

        if self.is_edge_visible(source_node_id, target_node_id, label):
            return self.VISIBLE_EDGE_COLOR
        else:
            return self.UNVISIBLE_EDGE_COLOR

    def get_edge_arrow_color(self):
        return self.ARROW_COLOR

    def get_selected_node_id(self):
        return self.selected_node_id

