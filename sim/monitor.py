
class Monitor():
    def __init__(self):
        self.monitors = {}
        self._create_monitors()
    
    def _create_monitors(self):
        available_monitors = ["memory_usage",
                              "memory_push",
                              "memory_pop",
                              "edges_calculated",
                              "edge_discovered",
                              "edge_completed"]
        for m in available_monitors:
            self.monitors[m] = []

    def push(self, monitor_name, xval, yval):
        if self.monitors.has_key(monitor_name):
            self.monitors[monitor_name].append((xval, yval))

    def get_monitor_data(self, monitor_type):
        if self.monitors.has_key(monitor_type):
            return self.monitors[monitor_type]

    def get_data(self, monitor_type):
        if self.monitors.has_key(monitor_type):
            xdata = []
            ydata = []
            for x, y in self.monitors[monitor_type]:
                xdata.append(x)
                ydata.append(y)
            return xdata, ydata
        return None