import process
import storage
import random as r

class Algorithm1(process.GraphProcess):
    NAME = "Algorithm 1"
    DESCRIPTION = "If process has more then 1 task to do, he try to send new \
task to another process which is waiting for work."

    def __init__(self, id, ctx):
        process.GraphProcess.__init__(self, id, self.NAME, ctx)
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
                    for p in self.communicator.get_processes():
                        if p.storage.get_size() == 0:
                            self.communicator.send_node(node, p.id)
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
                            processes = self.communicator.get_processes()
                            p = processes[i]
                            self.communicator.send_node(new_node, p.id)
            else:
                yield self.wait()

    def partition(self, node):
        max = len(self.communicator.get_processes()) - 1
        if max > 0:
            return r.randint(0, max)
        return 0


class Algorithm3(process.GraphProcess):
    NAME = "Alg 3"
    DESCRIPTION = "Sending new node to next process"

    def __init__(self, id, env, graph):
        process.GraphProcess.__init__(self, id, self.NAME, env, graph)
        self.storage = storage.QueueStorage()

    def initialize(self):
        if self.get_id() == 0:
            self.storage.put(self.graph.root)
            self.graph.root.discover(self.id)

    def run(self):
        process_count = self.get_world_comunicator().get_process_count()
        while True:
            self.clock.tick()
            if self.storage.get_size() > 0:
                node = self.storage.get()
                for edge in node.get_edges():
                    yield self.solve_edge(edge)
                    new_node = edge.get_destination()
                    if not new_node.is_discovered():
                        next = self.id + 1 % process_count
                        if next != self.id:
                            self.communicator.send_node(new_node, next)
                            new_node.discover(next)
                        else:
                            new_node.discover(self.id)
                        self.storage.put(new_node)
            else:
                yield self.wait()

class PingPongExample(process.GraphProcess):
    NAME = "PingPong"
    DESCRIPTION = "Example of using blocking 'send' and 'receive' message in process"

    def __init__(self, id, env, graph):
        process.GraphProcess.__init__(self, id, self.NAME, env, graph)

    def run(self):
        process_count = self.get_world_comunicator().get_process_count()
        if process_count < 2:
            self.log("need atleast two processes for pingpong", "err")
            yield self.wait()

        PING_PONG_LIMIT = 10
        world_rank = self.id
        ping_pong_count = 0
        partner_rank = (world_rank + 1) % 2
        while (ping_pong_count < PING_PONG_LIMIT):
            print self.communicator.get_waiting_messages_count()
            if (world_rank == ping_pong_count % 2):
                ping_pong_count += 1
                yield self.communicator.send(ping_pong_count, partner_rank)
                self.log("{0} send incremented value {1} to process {2}".format(world_rank,
                                                                                  ping_pong_count,
                                                                                  partner_rank))
            else:
                val = yield self.communicator.receive(partner_rank)
                val = val.data
                ping_pong_count = val
                self.log("{0} received {1} from process {2}".format(world_rank,
                                                                    ping_pong_count,
                                                                    partner_rank))
