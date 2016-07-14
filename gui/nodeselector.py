
class NodeSelector():
    def __init__(self, visible_graph):
        self.graph = visible_graph

    def get_node_at(self, x, y):
        for node in self.graph.nodes.values():
            nx = node.x
            ny = node.y
            nw = node.width
            nh = node.height

            if x >= nx and x <= nx + nw and y >= ny and y <= ny + nh:
                return node
        return None
                