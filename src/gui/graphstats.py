from misc import utils, colors


class GraphStats():
    def __init__(self, graph):
        self.nodes_count = graph.get_nodes_count()
        self.edges_count = graph.get_edges_count()
        self.undiscovered_nodes_count = self.nodes_count
        self.undiscovered_edges_count = self.edges_count
        self.calculated_edges_count = 0
        self.discovered_nodes = {} # key-> node id, value -> list of discoverers
        self.discovered_edges = {} # key-> edge id, value -> list of discoverers
        self.calculated_edges = {} # key-> edge id, value -> list of completers

    def discover_node(self, node_id, process_id):
        discoverers = self.discovered_nodes.get(node_id)
        if discoverers:
            discoverers.append(process_id)
        else:
            self.discovered_nodes[node_id] = [process_id]
        self.undiscovered_nodes_count -= 1

    def discover_edge(self, source_node_id, target_node_id, label, process_id):
        discoverers = self.discovered_edges.get((source_node_id, target_node_id, label))
        if discoverers:
            discoverers.append(process_id)
        else:
            self.discovered_edges[(source_node_id, target_node_id, label)] = [process_id]
        self.undiscovered_edges_count -= 1

    def calculate_edge(self, source_node_id, target_node_id, label, process_id):
        calculators = self.calculated_edges.get((source_node_id, target_node_id, label))
        if calculators:
            calculators.append(process_id)
        else:
            self.calculated_edges[(source_node_id, target_node_id, label)] = [process_id]
        self.calculated_edges_count += 1

    def is_node_discovered(self, node_id):
        return node_id in self.discovered_nodes

    def is_edge_discovered(self, source_node_id, target_node_id, label):
        return (source_node_id, target_node_id, label) in self.discovered_edges

    def is_edge_calculated(self, source_node_id, target_node_id, label):
        return (source_node_id, target_node_id, label) in self.calculated_edges

    def get_node_discoverer(self, node_id):
        return self.discovered_nodes.get(node_id)

    def get_edge_discoverer(self, source_node_id, target_node_id, label):
        return self.discovered_edges.get((source_node_id, target_node_id, label))

    def get_edge_calculator(self, source_node_id, target_node_id, label):
        return self.calculated_edges.get((source_node_id, target_node_id, label))

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

    def get_discovered_edges_count(self):
        return self.edges_count - self.undiscovered_edges_count

    def get_calculated_edges_count(self):
        return self.calculated_edges_count

    def get_discovered_nodes_by_process(self, process_id):
        return self._count_by_process_id(process_id, self.discovered_nodes)

    def get_discovered_edges_by_process(self, process_id):
        return self._count_by_process_id(process_id, self.discovered_edges)

    def get_calculated_edges_by_process(self, process_id):
        return self._count_by_process_id(process_id, self.calculated_edges)

    def reset(self):
        self.undiscovered_nodes_count = self.nodes_count
        self.undiscovered_edges_count = self.edges_count
        self.calculated_edges_count = 0
        self.discovered_nodes = {}
        self.calculated_edges = {}
        self.discovered_edges = {}

    def _count_by_process_id(self, process_id, dictionary):
        c = 0
        for _, v in dictionary.iteritems():
            if process_id in v:
                c += 1
        return c


class VisualGraphStats(GraphStats):

    UNVISIBLE_NODE_COLOR = (230, 230, 230)
    SELECTED_NODE_COLOR = (99, 99, 99)

    ARROW_COLOR = (255, 255, 255)
    UNVISIBLE_EDGE_COLOR = (230, 230, 230)
    VISIBLE_EDGE_COLOR = (160, 160, 160)

    MULTI_DISCOVERERS_EDGE_COLOR = (0, 0, 0)
    MULTI_DISCOVERERS_NODE_COLOR = (0, 0, 0)
    MULTI_CALCULATORS_EDGE_COLOR = (0, 0, 0)

    def __init__(self, graph, colors_count):
        GraphStats.__init__(self, graph)
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
        self.visible_edges = {}
        self.selected_node_id = None

    def is_node_visible(self, node_id):
        return self.is_node_discovered(node_id)

    def is_edge_visible(self, source_node_id, target_node_id, label):
        return (source_node_id, target_node_id, label) in self.visible_edges

    def is_selected_node(self, node_id):
        return self.selected_node_id and self.selected_node_id == node_id

    def get_node_color(self, node_id):
        discoverer = self.get_node_discoverer(node_id)
        if discoverer is not None:
            if len(discoverer) > 1:
                return self.MULTI_DISCOVERERS_NODE_COLOR
            return self.colors[discoverer[0]]

        return self.UNVISIBLE_NODE_COLOR

    def get_inverted_color(self, color):
        return utils.get_inverted_color(color)

    def get_edge_color(self, source_node_id, target_node_id, label):
        completers = self.get_edge_calculator(source_node_id, target_node_id, label)
        if completers is not None:
            if len(completers) > 1:
                return self.MULTI_CALCULATORS_EDGE_COLOR
            return self.colors[completers[0]]

        discoverer = self.get_edge_discoverer(source_node_id, target_node_id, label)
        if discoverer is not None:
            if len(discoverer) > 1:
                return self.MULTI_DISCOVERERS_EDGE_COLOR
            return self.colors[discoverer[0]]

        if self.is_edge_visible(source_node_id, target_node_id, label):
            return self.VISIBLE_EDGE_COLOR
        else:
            return self.UNVISIBLE_EDGE_COLOR

    def get_edge_arrow_color(self):
        return self.ARROW_COLOR

    def get_selected_node_id(self):
        return self.selected_node_id

