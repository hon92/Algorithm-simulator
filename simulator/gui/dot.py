

class DotGraphBuilder():
    def __init__(self, graph, dot_filename):
        self.graph = graph
        self.dot_file = dot_filename

    def _start(self):
        return "digraph g\n{\n"

    def _end(self):
        return "}\n"

    def _init(self):
        return "node[shape=\"box\"];\n"

    def _edge(self, from_node, edge):
        return from_node + " -> " + edge.get_target().id + " [label=\"" + str(edge.label) + "\"];\n" 

    def _node(self, node):
        return node.id + ";\n"

    def build(self):
        data = []
        data.append(self._start())
        data.append(self._init())
        
        temp = []
        for node in self.graph.nodes.values():
            data.append(self._node(node))
            for e in node.get_edges():
                temp.append(self._edge(node.id, e))

        data.extend(temp)
        data.append(self._end())
        return "".join(data)

    def write(self):
        with open(self.dot_file, "w") as f:
            f.write(self.build())