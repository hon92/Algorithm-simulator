import process
import storage
import random as r

class Algorithm1(process.GraphProcess):
    NAME = "Algorithm 1"
    DESCRIPTION = "If process has more then 1 task to do, he try to send new \
task to another process which is waiting for work."

    def __init__(self, id, env, graph):
        process.GraphProcess.__init__(self, id, self.NAME, env, graph)
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


class Algorithm2(process.GraphProcess):
    NAME = "SpinProcess"
    DESCRIPTION = "Spin process uses 'partition' function which deside where the process \
send new task."

    def __init__(self, id, env, graph):
        process.GraphProcess.__init__(self, id, self.NAME, env, graph)
        self.storage = storage.StackStorage()

    def initialize(self):
        if self.id == 0:
            self.storage.put(self.graph.root)

    def run(self):
        while True:
            self.clock.tick()
            if self.storage.get_size() > 0:
                node = self.storage.get()
                if not node.is_discovered():
                    node.discover(self.id)

                    for edge in node.get_edges():
                        edge.discover(self.id)
                        yield self.solve_edge(edge)
                        new_node = edge.get_destination()
                        i = self.partition(new_node)
                        if i == self.id:
                            self.storage.put(new_node)
                        else:
                            processes = self.comunicator.get_processes()
                            p = processes[i]
                            self.comunicator.send(new_node, p)
                            p.notify()
            else:
                yield self.wait()

    def partition(self, node):
        max = len(self.comunicator.get_processes()) - 1
        if max > 0:
            return r.randint(0, max)
        return 0

class Algorithm3(process.GraphProcess):
    NAME = "Alg 3"
    DESCRIPTION = "Testing alg"

    def __init__(self, id, env, graph):
        process.GraphProcess.__init__(self, id, self.NAME, env, graph)
        self.storage = storage.QueueStorage()

    def initialize(self):
        if self.get_id() == 0:
            self.storage.put(self.graph.root)
            self.graph.root.discover(self.id)

    def run(self):
        while True:
            self.clock.tick()
            if self.storage.get_size() > 0:
                node = self.storage.get()
                for edge in node.get_edges():
                    yield self.solve_edge(edge)
                    new_node = edge.get_destination()
                    if not new_node.is_discovered():
                        new_node.discover(self.id)
                        self.storage.put(new_node)
            else:
                yield self.wait()