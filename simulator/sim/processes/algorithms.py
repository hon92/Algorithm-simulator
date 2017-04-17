from simulator.public_api import process
import random as r


class Algorithm1(process.StorageProcess):

    NAME = "Algorithm 1"
    DESCRIPTION = "If process has more then 'busy_task_count' task to do, he try to send new \
task to another process which is waiting for work."
    PARAMS = {"busy_task_count": (1, int)}

    def __init__(self, id, ctx):
        process.StorageProcess.__init__(self, id, self.NAME, ctx, process.QueueStorage(self))

    def init(self):
        if self.get_id() == 0:
            root = self.ctx.graph.get_root()
            self.storage.put(root)
            self.ctx.graph_stats.discover_node(root, self)

    def run(self):
        gs = self.ctx.graph_stats

        while True:
            self.clock.tick()
            if self.storage.get_size() > 0:
                node = self.storage.get()
                if self.storage.get_size() > self.ctx.arguments["busy_task_count"]:
                    found = False
                    for p in self.ctx.processes:
                        if p.storage.get_size() == 0:
                            yield self.communicator.async_send(node, p.id)
                            found = True
                            break
                    if found:
                        continue

                for edge in node.get_edges():
                    yield self.solve_edge(edge)
                    new_node = edge.get_target()
                    if gs.is_node_discovered(new_node):
                        continue
                    gs.discover_node(new_node, self)
                    self.storage.put(new_node)
            else:
                yield self.wait()


class Algorithm2(process.StorageProcess):

    NAME = "Algorithm 2"
    DESCRIPTION = "Algorithm implemented according to the Spin algorithm. \
Algorithm uses 'partition' function for deciding, which \
process should utilize new node."
    PARAMS = {}

    def __init__(self, id, ctx):
        process.StorageProcess.__init__(self, id, self.NAME, ctx, process.StackStorage(self))

    def init(self):
        if self.get_id() == 0:
            root = self.ctx.graph.get_root()
            self.storage.put(root)

    def run(self):
        gs = self.ctx.graph_stats
        while True:
            self.clock.tick()
            if self.storage.get_size() > 0:
                node = self.storage.get()
                if not gs.is_node_discovered(node):
                    gs.discover_node(node, self)
                    for edge in node.get_edges():
                        yield self.solve_edge(edge)
                        new_node = edge.get_target()
                        i = self.partition(new_node)
                        if i == self.id:
                            self.storage.put(new_node)
                        else:
                            processes = self.ctx.processes
                            p = processes[i]
                            yield self.communicator.async_send(new_node, p.id)
            else:
                yield self.wait()

    def partition(self, node):
        max = len(self.ctx.processes) - 1
        if max > 0:
            return r.randint(0, max)
        return 0


class Algorithm3(process.StorageProcess):

    NAME = "Algorithm 3"
    DESCRIPTION = "Process send new discovered node to \
next process in simulation for utilize that node."
    PARAMS = {}

    def __init__(self, id, ctx):
        process.StorageProcess.__init__(self, id, self.NAME, ctx, process.QueueStorage(self))

    def init(self):
        if self.get_id() == 0:
            root = self.ctx.graph.get_root()
            self.storage.put(root)
            self.ctx.graph_stats.discover_node(root, self)

    def run(self):
        process_count = len(self.ctx.processes)
        gs = self.ctx.graph_stats
        while True:
            self.clock.tick()
            if self.storage.get_size() > 0:
                node = self.storage.get()
                for edge in node.get_edges():
                    if not gs.is_edge_discovered(edge):
                        yield self.solve_edge(edge)

                    new_node = edge.get_target()
                    if not gs.is_node_discovered(new_node):
                        next = (self.id + 1) % process_count
                        if next != self.id:
                            pr = self.ctx.processes[next]
                            gs.discover_node(new_node, pr)
                            yield self.communicator.async_send(new_node, next)
                        else:
                            gs.discover_node(new_node, self)
                        self.storage.put(new_node)
            else:
                yield self.wait()


class Aislinn(process.StorageProcess):

    NAME = "Algorithm 4"
    DESCRIPTION = "Algorithm with similar implementation like in tool Aislinn."
    PARAMS = {}

    def __init__(self, id, ctx):
        process.StorageProcess.__init__(
                self, id, self.NAME, ctx, process.QueueStorage(self))
        self.counter = 0

    def init(self):
        if self.get_id() == 0:
            root = self.ctx.graph.get_root()
            self.counter = 1
            self.ctx.graph_stats.discover_node(root, self)
            for edge in root.get_edges():
                self.storage.put((root, edge))

    def run(self):
        gs = self.ctx.graph_stats
        processes = self.ctx.processes
        storage = self.storage

        while True:
            self.clock.tick()

            while (self.communicator.get_n_messages() or
                   storage.get_size() == 0):
                target = (yield self.communicator.receive()).data
                storage.put(target)

            size = storage.get_size()
            assert self.counter == size, "counter != size"
            (node, edge) = storage.get()
            self.counter -= 1

            if size > 1:
                resend = False
                for i in xrange(1, len(processes)):
                    pid = (self.get_id() + i) % len(processes)
                    if processes[pid].counter == 0:
                        processes[pid].counter = 1
                        self.log("RESEND: " + str(self.get_id()) + " " + str(pid))
                        yield self.communicator.send((node, edge), pid)
                        resend = True
                        break
                if resend:
                    resend = True

            yield self.solve_edge(edge)
            target = edge.get_target()
            if gs.is_node_discovered(target):
                continue
            gs.discover_node(target, self)
            for edge in target.get_edges():
                storage.put((target, edge))
                self.counter += 1

