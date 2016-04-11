import process
from collections import deque

class MyProcess(process.Process):
    def __init__(self, env):
        process.Process.__init__(self, env)

    def get_name(self):
        return "MyProcess"
    
    def on_start(self):
        if self.id == 0:
            self.queue = deque([self.graph.root])
            self.graph.root.discover(0)
        else:
            self.queue = deque([])
        self.messages = []

    def run(self):
        while True:
            self.add_step()
            self.send_monitor_data("memory_usage", self.get_step(), len(self.queue))
            if len(self.queue) > 0:
                node = self.queue.popleft()
                self.send_monitor_data("memory_pop", self.get_step(), len(self.queue))
                if len(self.queue) > 1:
                    found = False
                    for p in self.processes:
                        if len(p.queue) == 0:
                            p.messages.append(node)
                            p.unblock()
                            found = True
                            break
                    if found:
                        continue

                for transition in node.get_edges():
                    transition.discover(self.id)
                    self.send_monitor_data("edge_discovered", self.get_step(), self.edges_calculated)
                    yield self.env.timeout(transition.get_time())
                    self.calculate_edge(transition.get_time())
                    transition.complete(self.id)
                    self.send_monitor_data("edge_completed", self.get_step(), self.edges_calculated)
                    self.send_monitor_data("edges_calculated", self.get_time(), self.edges_calculated)
                    new_node = transition.get_destination()
                    if new_node.is_discovered():
                        continue
                    new_node.discover(self.id)
                    self.queue.append(new_node)
                    self.send_monitor_data("memory_push", self.get_step(), len(self.queue))
            else:
                yield self.block_until()
                messages = self.messages
                self.messages = []
                for m in messages:
                    self.queue.append(m)
                    self.send_monitor_data("memory_usage", self.get_step(), len(self.queue))
                self.send_monitor_data("memory_push", self.get_step(), len(self.queue))
                self.reset_block()
