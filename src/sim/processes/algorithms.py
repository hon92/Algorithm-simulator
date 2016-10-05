import process
import random as r


class Algorithm1(process.GraphProcess):

    NAME = "Algorithm 1"
    DESCRIPTION = "If process has more then 1 task to do, he try to send new \
task to another process which is waiting for work."
    PARAMS = {}

    def __init__(self, id, ctx):
        process.GraphProcess.__init__(self, id, self.NAME, ctx, process.QueueStorage())

    def init(self):
        if self.get_id() == 0:
            root = self.ctx.graph.get_root()
            self.storage.put(root)
            self.ctx.graph_stats.discover_node(root.get_id(), 0)

    def run(self):
        gs = self.ctx.graph_stats
        while True:
            self.clock.tick()
            if self.storage.get_size() > 0:
                node = self.storage.get()
                if self.storage.get_size() > 1:
                    found = False
                    for p in self.ctx.processes:
                        if p.storage.get_size() == 0:
                            self.communicator.isend(node, p.id)
                            found = True
                            break
                    if found:
                        continue

                for edge in node.get_edges():
                    yield self.solve_edge(edge)
                    new_node = edge.get_target()
                    if gs.is_node_discovered(new_node.get_id()):
                        continue
                    gs.discover_node(new_node.get_id(), self.id)
                    self.storage.put(new_node)
            else:
                yield self.wait()


class Algorithm2(process.GraphProcess):

    NAME = "SpinProcess"
    DESCRIPTION = "Spin process uses 'partition' function which deside where the process \
send new task."
    PARAMS = {}

    def __init__(self, id, ctx):
        process.GraphProcess.__init__(self, id, self.NAME, ctx, process.StackStorage())

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
                if not gs.is_node_discovered(node.id):
                    gs.discover_node(node.id, self.id)

                    for edge in node.get_edges():
                        yield self.solve_edge(edge)
                        new_node = edge.get_target()
                        i = self.partition(new_node)
                        if i == self.id:
                            self.storage.put(new_node)
                        else:
                            processes = self.ctx.processes
                            p = processes[i]
                            self.communicator.isend(new_node, p.id)
            else:
                yield self.wait()

    def partition(self, node):
        max = len(self.ctx.processes) - 1
        if max > 0:
            return r.randint(0, max)
        return 0


class Algorithm3(process.GraphProcess):

    NAME = "Alg 3"
    DESCRIPTION = "Sending new node to next process"
    PARAMS = {}

    def __init__(self, id, ctx):
        process.GraphProcess.__init__(self, id, self.NAME, ctx, process.QueueStorage())

    def init(self):
        if self.get_id() == 0:
            root = self.ctx.graph.get_root()
            self.storage.put(root)
            self.ctx.graph_stats.discover_node(root.get_id(), self.get_id())

    def run(self):
        process_count = len(self.ctx.processes)
        gs = self.ctx.graph_stats
        while True:
            self.clock.tick()
            if self.storage.get_size() > 0:
                node = self.storage.get()
                for edge in node.get_edges():
                    yield self.solve_edge(edge)
                    new_node = edge.get_target()
                    if not gs.is_node_discovered(new_node.id):
                        next = self.id + 1 % process_count
                        if next != self.id:
                            self.communicator.isend(new_node, next)
                            gs.discover_node(new_node.id, next)
                        else:
                            gs.discover_node(new_node.id, self.id)
                        self.storage.put(new_node)
            else:
                yield self.wait()


class PingPongExample(process.GraphProcess):

    NAME = "PingPong"
    DESCRIPTION = "Example of using blocking 'send' and 'receive' message in process"
    PARAMS = {}

    def __init__(self, id, ctx):
        process.GraphProcess.__init__(self, id, self.NAME, ctx, process.QueueStorage())

    def run(self):
        process_count = len(self.ctx.processes)
        if process_count < 2:
            self.log("need atleast two processes for pingpong", "err")
            yield self.wait()

        PING_PONG_LIMIT = 10
        world_rank = self.id
        ping_pong_count = 0
        partner_rank = (world_rank + 1) % 2
        while (ping_pong_count < PING_PONG_LIMIT):
            if (world_rank == ping_pong_count % 2):
                ping_pong_count += 1
                yield self.communicator.send(ping_pong_count, partner_rank)
                self.log("{0} send incremented value {1} to process {2}".format(world_rank,
                                                                                ping_pong_count,
                                                                                partner_rank))
            else:
                val = yield self.communicator.receive(partner_rank)
                if val:
                    val = val.data
                    ping_pong_count = val
                    self.log("{0} received {1} from process {2}".format(world_rank,
                                                                        ping_pong_count,
                                                                        partner_rank))

