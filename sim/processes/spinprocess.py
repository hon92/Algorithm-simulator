import process
import random as r

class SPINProcess(process.Process):
    def __init__(self, env):
        process.Process.__init__(self, env)

    def get_name(self):
        return "SPIN"

    def on_start(self):
        self.queue = []
        if self.id == 0:
            self.queue.append(self.graph.root)
        self.messages = []

    def run(self):
        while True:
            self.add_step()
            self.send_monitor_data("memory_usage", self.get_step(), len(self.queue))
            if len(self.queue) > 0:
                node = self.queue.pop()
                self.send_monitor_data("memory_pop", self.get_step(), len(self.queue))
                if not node.is_discovered():
                    node.discover(self.id)

                    for transition in node.get_edges():
                        transition.discover(self.id)
                        self.send_monitor_data("edge_discovered", self.get_step(), self.edges_calculated)
                        yield self.env.timeout(transition.get_time())
                        self.calculate_edge(transition.get_time())
                        transition.complete(self.id)
                        self.send_monitor_data("edge_completed", self.get_step(), self.edges_calculated)
                        self.send_monitor_data("edges_calculated", self.get_time(), self.edges_calculated)
                        new_node = transition.get_destination()
                        i = self.partition(new_node)
                        if i == self.id:
                            self.queue.append(new_node)
                            self.send_monitor_data("memory_push", self.get_step(), len(self.queue))
                        else:
                            p = self.processes[i]
                            p.messages.append(new_node)
                            p.unblock()
            else:
                yield self.block_until()
                messages = self.messages
                self.messages = []
                for m in messages:
                    self.queue.append(m)
                    self.send_monitor_data("memory_usage", self.get_step(), len(self.queue))
                self.send_monitor_data("memory_push", self.get_step(), len(self.queue))
                self.reset_block()

    def partition(self, node):
        return r.randint(0, len(self.processes) - 1)
