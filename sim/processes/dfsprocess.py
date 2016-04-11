import process

class DFSProcess(process.Process):
    def __init__(self, env):
        process.Process.__init__(self, env)

    def on_start(self):        
        self.stack = []
        if self.id == 0:
            self.stack.append(self.graph.root)
        self.messages = []

    def run(self):
        while True:
            self.send_monitor_data("memory_usage", len(self.stack))
            if len(self.stack) > 0:
                node = self.stack.pop()
                if not node.found:
                    node.found = True
                    yield self.env.timeout(node.complexity)
                    self.calculated += node.complexity
                    self.send_monitor_data("nodes_calculated", self.calculated)
                    
                    for transition in node.get_edges():
                        yield self.env.timeout(transition.complexity)
                        self.calculated += transition.complexity
                        self.send_monitor_data("nodes_calculated", self.calculated)
                        new_node = transition.get_destination()
                        self.stack.append(new_node)                    
            else:
                yield self.block_until()
                messages = self.messages
                self.messages = []
                for m in messages:
                    self.stack.append(m)
                self.reset_block()