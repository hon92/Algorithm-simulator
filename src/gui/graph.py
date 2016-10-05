

class Graph():
    def __init__(self):
        self.nodes = {} # key -> node id, value -> node
        self.root = None

    def set_root_node(self, id):
        if id in self.nodes:
            self.root = self.nodes[id]
        else:
            raise Exception("Invalid root node id")

    def get_root(self):
        return self.root

    def add_node(self, node):
        if node.id not in self.nodes:
            self.nodes[node.id] = node
        else:
            raise Exception("Node id already exists in graph")

    def get_node(self, id):
        if id in self.nodes:
            return self.nodes[id]
        return None

    def add_edge(self, edge):
        if edge.source.id in self.nodes:
            self.nodes[edge.source.id].add_edge(edge)
        else:
            raise Exception("Source node of edge not exists in graph")

    def get_edge(self, source_node_id, target_node_id):
        if source_node_id in self.nodes and target_node_id in self.nodes:
            source_node_edges = self.nodes[source_node_id].get_edges()

            for edge in source_node_edges:
                if edge.get_target().id == target_node_id:
                    return edge
        return None

    def get_nodes_count(self):
        return len(self.nodes)

    def get_edges_count(self):
        edges_count = 0
        for _, node in self.nodes.iteritems():
            edges_count += len(node.get_edges())
        return edges_count


class Node():
    def __init__(self, id, size):
        self.id = id
        self.edges = None
        self.size = size

    def get_edges(self):
        if not self.edges:
            self.edges = []
        return self.edges

    def add_edge(self, edge):
        self.get_edges().append(edge)

    def get_size(self):
        return self.size

    def get_id(self):
        return self.id


class Edge():
    def __init__(self, source, target, time, events_count, pids, label):
        self.source = source
        self.target = target
        self.time = time
        self.events_count = events_count
        self.pids = pids
        self.label = label

    def get_source(self):
        return self.source

    def get_target(self):
        return self.target

    def get_time(self):
        return self.time

    def get_label(self):
        return self.label

    def get_events_count(self):
        return self.events_count

    def get_pids(self):
        return self.pids


class VisibleGraph(Graph):
    def __init__(self, scale, width, height):
        Graph.__init__(self)
        self.scale = scale
        self.width = width
        self.height = height

    def draw(self, canvas, vis_graph_stats):
        for _, node in self.nodes.iteritems():
            node.draw(canvas, vis_graph_stats)


class VisibleNode(Node):
    def __init__(self, id, size, x, y, width, height):
        Node.__init__(self, id, size)
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self, canvas, vis_graph_stats):
        color = vis_graph_stats.get_node_color(self.id)
        canvas.set_color(*color)
        canvas.draw_rectangle(self.x,
                              self.y,
                              self.width,
                              self.height,
                              True)

        inv_color = vis_graph_stats.get_inverted_color(color)
        canvas.set_color(*inv_color)
        canvas.draw_centered_text(self.x + self.width / 2,
                                  self.y + self.height / 2,
                                  "id:{0}".format(self.id, self.get_size()))

        if vis_graph_stats.is_selected_node(self.id):
            canvas.draw_rectangle(self.x - 1,
                                  self.y - 1,
                                  self.width + 1,
                                  self.height + 1)
        for e in self.get_edges():
            if vis_graph_stats.is_node_visible(e.get_target().get_id()):
                vis_graph_stats.set_edge_visibility(e.source.id,
                                                    e.target.id,
                                                    e.label, vis_graph_stats.is_node_visible(self.id))
            e.draw(canvas, vis_graph_stats)


class VisibleEdge(Edge):
    def __init__(self, source, target, time, events_count, pids, label,
                 lx, ly, points, arrow_polygon):
        Edge.__init__(self, source, target, time, events_count, pids, label)
        self.lx = lx
        self.ly = ly
        self.label = label
        self.points = points
        self.arrow_polygon = arrow_polygon

    def draw(self, canvas, vis_graph_stats):
        edge_id = (self.source.id, self.target.id, self.label)
        edge_color = vis_graph_stats.get_edge_color(*edge_id)
        arrow_color = vis_graph_stats.get_edge_arrow_color()
        is_discovered = vis_graph_stats.is_edge_discovered(*edge_id)
        is_completed = vis_graph_stats.is_edge_calculated(*edge_id)
        dashed =  is_discovered and not is_completed
        discoverer = vis_graph_stats.get_edge_discoverer(*edge_id)
        completer = vis_graph_stats.get_edge_calculator(*edge_id)

        if discoverer is None:
            discoverer = -1
        if completer is None:
            completer = -1

        if dashed:
            dashed = "dash"

        discoverers = vis_graph_stats.get_edge_discoverer(*edge_id)
        if discoverers and len(discoverers) > 1:
            dashed = "dots"

        label = "({0})->({1})".format(discoverer, completer)
        canvas.set_color(*edge_color)
        canvas.draw_text(self.lx, self.ly, label)
        canvas.set_color(*arrow_color)
        canvas.draw_polygon(self.arrow_polygon, True)
        canvas.set_color(*edge_color)
        canvas.draw_path(self.points, dashed)

