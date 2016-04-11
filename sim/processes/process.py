
class Process():
    def __init__(self, env):
        self.env = env
        self.block_event = env.event()
        self.edges_calculated = 0
        self.step = 0

    def on_start(self):
        pass

    def run(self):
        yield

    def send_monitor_data(self, monitor_type, xval, yval):
        self.monitor.push(monitor_type, xval, yval)

    def get_time(self):
        return self.env.now

    def get_step(self):
        return self.step

    def add_step(self):
        self.step += 1

    def block_until(self):
        return self.block_event

    def unblock(self):
        if not self.block_event.triggered:
            self.block_event.succeed()

    def reset_block(self):
        self.block_event = self.env.event()

    def calculate_edge(self, val):
        self.edges_calculated += val

    def get_name(self):
        return ""

    def get_calculated_time(self):
        return self.edges_calculated

