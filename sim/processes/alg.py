import process
import storage

class Alg2(process.GraphProcess):
    def __init__(self, id, env, graph):
        process.GraphProcess.__init__(self, id, "Alg2", env, graph)
        self.storage = storage.QueueStorage()

    def initialize(self):
        if self.get_id() == 0:
            self.storage.put(self.graph.root)
            self.graph.root.discover(0)

    def run(self):
        while True:
            self.clock.tick()
            if self.storage.get_size() > 0:
                node = self.storage.get()
                if self.storage.get_size() > 1:
                    found = False
                    for p in self.comunicator.get_processes():
                        if p.storage.get_size() == 0:
                            self.comunicator.send(node, p)
                            p.notify()
                            found = True
                            break
                    if found:
                        continue

                for edge in node.get_edges():
                    yield self.solve_edge(edge)
                    new_node = edge.get_destination()
                    if new_node.is_discovered():
                        continue
                    new_node.discover(self.id)
                    self.storage.put(new_node)
            else:
                yield self.wait()
