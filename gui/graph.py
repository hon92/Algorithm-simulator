from collections import deque

class Graph():
    def __init__(self):
        self.nodes = {} # key -> node.id, value -> node
        self.root = None
        self.edges_count = None
        self.discovered_nodes_count = 0

    def set_root_node(self, name):
        if name in self.nodes:
            self.root = self.nodes[name]
        else:
            raise Exception("Invalid root node")

    def get_root(self):
        return self.root

    def add_node(self, node):
        if node.name not in self.nodes:
            self.nodes[node.name] = node

    def get_node(self, name):
        if name in self.nodes:
            return self.nodes[name]
        return None

    def add_edge(self, node_name, edge):
        if node_name in self.nodes:
            self.nodes[node_name].add_edge(edge)

    def get_edge(self, source_node, destination_node):
        if source_node in self.nodes and destination_node in self.nodes:
            for edge in self.nodes[source_node].get_edges():
                if edge.get_destination().name == destination_node:
                    return edge
        return None

    def reset(self):
        self.discovered_nodes_count = 0
        for n, node in self.nodes.iteritems():
            node.discover(-1)
            for edge in node.get_edges():
                edge.discover(-1)
                edge.complete(-1)

    def get_nodes_count(self):
        return len(self.nodes)

    def get_edges_count(self):
        if self.edges_count is not None:
            return self.edges_count
        edges = 0
        for name, node in self.nodes.iteritems():
            edges += len(node.get_edges())
        self.edges_count = edges
        return edges

    def get_discovered_nodes_count(self):
        return self.discovered_nodes_count

class Node():
    def __init__(self, name, size):
        self.name = name
        self.edges = None
        self.size = size
        self.discovered_by = -1

    def get_edges(self):
        if not self.edges:
            return []
        return self.edges

    def add_edge(self, edge):
        if not self.edges:
            self.edges = []
        self.edges.append(edge)

    def get_size(self):
        return self.size

    def get_name(self):
        return self.name

    def discover(self, by):
        self.discovered_by = by
        if by != -1:
            self.graph.discovered_nodes_count += 1

    def get_discoverer(self):
        return self.discovered_by

    def is_discovered(self):
        return self.discovered_by != -1

    def is_completed(self):
        for e in self.get_edges():
            if not e.is_completed():
                return False
        return True

class Edge():
    def __init__(self, destination, time, events_count, pids, label):
        self.destination = destination
        self.time = time
        self.events_count = events_count
        self.pids = pids
        self.label = label
        self.discovered_by = -1
        self.completed_by = -1

    def get_destination(self):
        return self.destination

    def get_time(self):
        return self.time

    def is_discovered(self):
        return self.discovered != -1

    def get_discoverer(self):
        return self.discovered_by

    def is_completed(self):
        return self.completed_by != -1

    def get_complete(self):
        return self.completed_by

    def discover(self, by):
        self.discovered_by = by

    def complete(self, by):
        self.completed_by = by

class VisibleGraph(Graph):
    def __init__(self, scale, width, height):
        Graph.__init__(self)
        self.scale = scale
        self.width = width
        self.height = height
        self.node_colors = [(155, 155, 155)]

    def draw(self, canvas):
        for name, node in self.nodes.iteritems():
            node.draw(canvas)

    def reset(self):
        self.discovered_nodes_count = 0
        for n, node in self.nodes.iteritems():
            node.discover(-1)
            for edge in node.get_edges():
                edge.discover(-1)
                edge.complete(-1)
            node.set_visible(False)
        self.get_root().set_visible(True)

    def set_colors(self, colors):
        del self.node_colors[1:]
        for c in colors:
            self.node_colors.append(c)

class VisibleNode(Node):
    def __init__(self, name, complexity, x, y, width, height):
        Node.__init__(self, name, complexity)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = False

    def is_visible(self):
        return self.visible

    def set_visible(self, value):
        self.visible = value

    def discover(self, by):
        Node.discover(self, by)
        if by != -1:
            self.set_visible(True)

    def draw(self, canvas):
        color = self.graph.node_colors[0]
        name_color = (240, 255, 255)

        if self.is_visible():
            if self.discovered_by != -1:
                color = self.graph.node_colors[self.discovered_by + 1]

        canvas.set_color(*color)
        canvas.draw_rectangle(self.x,
                              self.y,
                              self.width,
                              self.height,
                              True)
        canvas.set_color(*name_color)
        canvas.draw_text(self.x + self.width / 6,
                         self.y + self.height / 2,
                         "'{0}'".format(self.name, self.get_size()))

        for e in self.get_edges():
            if e.get_destination().is_visible():
                e.set_visible(self.is_visible())
            e.draw(canvas)

class VisibleEdge(Edge):
    def __init__(self, destination, complexity, events_count, pids, label, lx, ly, points, arrow_polygon):
        Edge.__init__(self, destination, complexity, events_count, pids, label)
        self.label_x = lx
        self.label_y = ly
        self.label = label
        self.points = points
        self.arrow_polygon = arrow_polygon
        self.visible = False

    def set_visible(self, value):
        self.visible = value

    def draw(self, canvas):
        completed_by = self.get_complete()
        discovered_by = self.get_discoverer()
        text_color = (100, 75, 55)
        arrow_color = (255, 255, 255)
        edge_color = self.destination.graph.node_colors[0]

        if self.visible:
            edge_color = self.destination.graph.node_colors[self.destination.discovered_by + 1]
        
        if self.discovered_by != -1:
            edge_color = self.destination.graph.node_colors[self.discovered_by + 1]
            c = 120 # brightness constant
            edge_color = (int(edge_color[0] + c), int(edge_color[1] + c), int(edge_color[2] + c)) 
        if self.completed_by != -1:
            edge_color = self.destination.graph.node_colors[self.completed_by + 1]

        label = "({0})->({1})".format(discovered_by, completed_by)
        canvas.set_color(*text_color)
        canvas.draw_text(self.label_x, self.label_y, label)
        canvas.set_color(*arrow_color)
        canvas.draw_polygon(self.arrow_polygon, True)
        canvas.set_color(*edge_color)
        canvas.draw_path(self.points)

