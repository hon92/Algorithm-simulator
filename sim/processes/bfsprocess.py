import process
from collections import deque

class BFSProcess(process.Process):
    def __init__(self, env):
        process.Process.__init__(self, env)
    
    def on_start(self):
        if self.id == 0:
            self.queue = deque([self.graph.root])
            self.graph.root.found = True
        else:
            self.queue = deque([])
        self.messages = []
    
    def run(self):
        while True:
            self.send_monitor_data("memory_usage", len(self.queue))
            if len(self.queue) > 0:
                node = self.queue.popleft()
                yield self.env.timeout(node.complexity)
                self.calculated += node.complexity
                self.send_monitor_data("nodes_calculated", self.calculated)
  
                for transition in node.get_edges():
                    yield self.env.timeout(transition.complexity)
                    self.calculated += transition.complexity
                    self.send_monitor_data("nodes_calculated", self.calculated)
                    new_node = transition.get_destination()
                    if new_node.found:
                        continue
                    new_node.found = True
                    new_node.discovered_by = self.id
                    self.queue.append(new_node)
            else:
                yield self.block_until()
                messages = self.messages
                self.messages = []
                for m in messages:
                    self.queue.append(m)
                self.reset_block()
