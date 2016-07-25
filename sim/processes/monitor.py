class MonitorManager():
    def __init__(self):
        self.monitors = []

    def register_monitor(self, monitor):
        self.monitors.append(monitor)

    def unregister_monitor(self, monitor):
        if monitor in self.monitors:
            self.monitors.remove(monitor)

    def collect(self, monitors_to_collect = None):
        for mon in self.monitors:
            yield mon.collect(monitors_to_collect)

    def get_monitor(self, monitor_name):
        for m in self.monitors:
            if m.get_name() == monitor_name:
                return m
        return None


class Entry():
    def __init__(self, entry_name, args):
        self.entry_name = entry_name
        self.args = args

    def check(self, val):
        return len(val) == len(self.args)

class Monitor():
    def __init__(self, name):
        self.name = name
        self.data = {}
        self.entries = {}

    def get_name(self):
        return self.name

    def put(self, entry_name, val):
        if entry_name in self.entries:
            entry = self.entries[entry_name]
            if entry.check(val):
                self.data[entry_name].append(val)
            else:
                raise Exception("Invalid arguments for entry '" + entry_name + "'")

    def collect(self, monitors_to_collect = None):
        if monitors_to_collect:
            data = {}
            for m in monitors_to_collect:
                if m in self.data:
                    data[m] = self.data[m]
            return data
        return self.data

    def add_entry(self, name, *args):
        self.entries[name] = Entry(name, args)
        self.data[name] = []

    def set_enabled(self, enabled):
        self.enabled = enabled

    def is_enabled(self):
        return self.enabled

    def get_header_data(self):
        return ";".join(self.data.keys())

class TimeMonitor(Monitor):
    def __init__(self, clock):
        Monitor.__init__(self, "TimeMonitor")
        self.add_entry("wait", "current_time", "added_time")
        self.clock = clock
        self.clock.connect("wait", self.on_time_added)

    def on_time_added(self, current_time, added_time):
        self.put("wait", (current_time, added_time))

class MemoryMonitor(Monitor):
    def __init__(self, storage, clock):
        Monitor.__init__(self, "MemoryMonitor")
        self.add_entry("push_time", "simulation_time", "storage_size")
        self.add_entry("pop_time", "simulation_time", "storage_size")
        self.add_entry("push_step", "clock_step", "storage_size")
        self.add_entry("pop_step", "clock_step", "storage_size")
        self.add_entry("memory_usage_time", "simulation_time", "storage_size")
        self.add_entry("memory_usage_step", "clock_step", "storage_size")
        self.storage = storage
        self.clock = clock
        self.storage.connect("push", self.on_push)
        self.storage.connect("pop", self.on_pop)

    def on_push(self):
        self.put("push_time", (self.clock.get_simulation_time(), self.storage.get_size()))
        self.put("push_step", (self.clock.get_step(), self.storage.get_size()))

    def on_pop(self):
        self.put("pop_time", (self.clock.get_simulation_time(), self.storage.get_size()))
        self.put("pop_step", (self.clock.get_step(), self.storage.get_size()))


class EdgeMonitor(Monitor):
    def __init__(self, graph_process):
        Monitor.__init__(self, "EdgeMonitor")
        self.add_entry("edge_discovered", "simulation_time", "clock_time", "clock_step")
        self.add_entry("edge_calculated", "simulation_time", "clock_time", "clock_step", "edge_time")
        self.add_entry("edge_completed", "simulation_time", "clock_time", "clock_step")
        graph_process.connect("edge_discovered", self.on_edge_discovered)
        graph_process.connect("edge_calculated", self.on_edge_calculated)
        graph_process.connect("edge_completed", self.on_edge_completed)

    def on_edge_discovered(self, sim_time, process_time, process_step):
        self.put("edge_discovered", (sim_time, process_time, process_time))

    def on_edge_completed(self, sim_time, process_time, process_step):
        self.put("edge_completed", (sim_time, process_time, process_time))

    def on_edge_calculated(self, sim_time, process_time, process_step, edge_time):
        self.put("edge_calculated", (sim_time, process_time, process_time, edge_time))

class ProcessMonitor(Monitor):
    def __init__(self, process):
        Monitor.__init__(self, "ProcessMonitor")
        self.add_entry("wait", "simulation_time")
        self.add_entry("notify", "simulation_time")
        self.process = process
        self.process.connect("notify", self.on_notify)
        self.process.connect("wait", self.on_wait)

    def on_notify(self, time):
        self.put("notify", (time,))

    def on_wait(self, time):
        self.put("wait", (time,))

