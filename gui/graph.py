class Graph():
    def __init__(self):
        self.nodes = {} # key -> node.id, value -> node
        self.root = None

    def set_root_node(self, name):
        if self.nodes.has_key(name):
            self.root = self.nodes[name]
        else:
            raise Exception("Invalid root node")

    def get_root(self):
        return self.root

    def add_node(self, node):
        if not self.nodes.has_key(node.name):
            self.nodes[node.name] = node

    def get_node(self, name):
        if self.nodes.has_key(name):
            return self.nodes[name]
        return None

    def add_edge(self, node_name, edge):
        if self.nodes.has_key(node_name):
            self.nodes[node_name].add_edge(edge)

    def get_edge(self, source_node, destination_node):
        if self.nodes.has_key(source_node) and self.nodes.has_key(destination_node):
            for edge in self.nodes[source_node].get_edges():
                if edge.get_destination().name == destination_node:
                    return edge
        return None

    def reset(self):
        for node in self.nodes.values():
            node.discover(-1)
            for edge in node.get_edges():
                edge.discover(-1)
                edge.complete(-1)

class Node():
    def __init__(self, name, size):
        self.name = name
        self.edges = []
        self.size = size
        self.discovered_by = -1

    def get_edges(self):
        return self.edges

    def add_edge(self, edge):
        self.edges.append(edge)

    def get_size(self):
        return self.size

    def get_name(self):
        return self.name

    def discover(self, by):
        self.discovered_by = by

    def get_discoverer(self):
        return self.discovered_by

    def is_discovered(self):
        return self.discovered_by != -1

    def is_completed(self):
        for e in self.edges:
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

    def draw(self, canvas):
        for node in self.nodes.values():
            node.draw(canvas)

    def reset(self):
        for node in self.nodes.values():
            node.discover(-1)
            for edge in node.get_edges():
                edge.discover(-1)
                edge.complete(-1)
            node.set_visible(False)
        self.get_root().set_visible(True)
            
class VisibleNode(Node):
    def __init__(self, name, complexity, x, y, width, height):
        Node.__init__(self, name, complexity)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = False
        self.discovered_by = None
        self.succesors_count = 0

    def is_visible(self):
        return self.visible

    def set_visible(self, value):
        self.visible = value

    def get_succesors_count(self):
        return self.succesors_count

    def draw(self, canvas):
        if not self.is_visible():
            return
        r = 0
        g = 150
        b = 149
        if self.discovered_by:
            r += (self.discovered_by + 1) * 40
            g += (self.discovered_by + 1) * 40
        canvas.set_color(r, g, b)
        canvas.draw_rectangle(self.x, self.y, self.width, self.height, True)
        canvas.set_color(240, 255, 255)
        canvas.draw_text(self.x + self.width/6, self.y + self.height/2, "'{0}'".format(self.name, self.get_size()))
        canvas.draw_text(self.x, self.y + self.height, "{0}".format(self.succesors_count))

        for e in self.edges:
            if e.get_destination().is_visible():
                e.draw(canvas)

class VisibleEdge(Edge):
    def __init__(self, destination, complexity, events_count, pids, label, lx, ly, points, arrow_polygon):
        Edge.__init__(self, destination, complexity, events_count, pids, label)
        self.label_x = lx
        self.label_y = ly
        self.label = label
        self.points = points
        self.arrow_polygon = arrow_polygon

    def draw(self, canvas):
        completed_by = self.get_complete()
        discovered_by = self.get_discoverer()

        r = 0
        g = 150
        b = 149

        if completed_by != -1 and discovered_by != -1:            
            if self.discovered_by:
                r += (self.discovered_by + 1) * 40
                g += (self.discovered_by + 1) * 40
            canvas.set_color(r, g, b)
        else:
            canvas.set_color(0, 0, 0)

        label = "({0})->({1})".format(discovered_by, completed_by)
        canvas.draw_text(self.label_x, self.label_y, label)
        canvas.draw_polygon(self.arrow_polygon, True)
        canvas.draw_path(self.points)
        