import re


class MonitorManager():

    REGEX = "(^p)(\d+)(_)(\w+)"

    def __init__(self):
        self.monitors = {}
        self.listeners = {}
        self.process_listeners = {}

    def add_callback(self, event_name, object):
        if event_name in self.listeners:
            self.listeners[event_name].append(object)
        else:
            self.listeners[event_name] = [object]

    def add_process_callback(self, event_name, process_id, object):
        if process_id in self.process_listeners:
            listeners = self.process_listeners[process_id]
            if event_name in listeners:
                listeners[event_name].append(object)
            else:
                listeners[event_name]  = [object]
        else:
            self.process_listeners[process_id] = {event_name: [object]}

        self.add_callback(event_name, object)

    def connect(self, event_name, callback):
        m = re.match(self.REGEX, event_name)
        if m:
            pid = int(m.group(2))
            ev_name = m.group(4)
            if pid in self.process_listeners and ev_name in self.process_listeners[pid]:
                self._dispatch_process_callback(pid, ev_name, callback)
            else:
                raise Exception("Unknown process event name")
        else:
            if event_name in self.listeners:
                self._dispatch_event(event_name, callback)
            else:
                raise Exception("Unknown event name")

    def _dispatch_event(self, event_name, callback):
        source_objects = self.listeners[event_name]
        for object in source_objects:
            object.connect(event_name, callback)

    def _dispatch_process_callback(self, process_id, event_name, callback):
        listeners = self.process_listeners[process_id]
        source_objects = listeners[event_name]
        for object in source_objects:
            object.connect(event_name, callback)

    def register_process_monitor(self, pid, monitor):
        if pid not in self.monitors:
            self.monitors[pid] = [monitor]
        else:
            self.monitors[pid].append(monitor)

    def unregister_process_monitor(self, pid, monitor):
        if pid in self.monitors:
            monitors = self.monitors[pid]
            for m in monitors:
                if m == monitor:
                    monitors.remove(m)
                    break

    def collect(self, process_id, monitors_to_collect = None):
        process_monitors = self.monitors.get(process_id)
        if process_monitors:
            for m in process_monitors:
                yield m.collect(monitors_to_collect)

    def clear_monitors(self):
        self.monitors = {}

    def get_process_monitor(self, pid, monitor_name):
        if pid in self.monitors:
            monitors = self.monitors[pid]
            for m in monitors:
                if m.get_id() == monitor_name:
                    return m
        return None

    def get_process_monitors(self, process_id):
        return self.monitors.get(process_id)

    def clear_data(self):
        for pr_monitors in self.monitors.values():
            for m in pr_monitors:
                m.clear()


class Entry():
    def __init__(self, entry_name, args):
        self.entry_name = entry_name
        self.args = args

    def check(self, val):
        return len(val) == len(self.args)


class Monitor():
    def __init__(self, id, process):
        self.id = id
        self.process = process
        self.data = {}
        self.entries = {}

    def get_id(self):
        return self.id

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

    def clear(self):
        for measured_data in self.data.values():
            del measured_data[:]


class TimeMonitor(Monitor):
    def __init__(self, process):
        Monitor.__init__(self, "TimeMonitor", process)
        self.add_entry("time_added", "current_time", "added_time")
        self.process.clock.connect("time_added", self.on_time_added)

    def on_time_added(self, current_time, added_time):
        self.put("time_added", (current_time, added_time))


class MemoryMonitor(Monitor):
    def __init__(self, process):
        Monitor.__init__(self, "MemoryMonitor", process)
        self.add_entry("push_time", "item", "simulation_time", "storage_size")
        self.add_entry("pop_time", "item", "simulation_time", "storage_size")
        self.add_entry("push_step", "item", "clock_step", "storage_size")
        self.add_entry("pop_step", "item", "clock_step", "storage_size")
        self.add_entry("memory_usage_time", "simulation_time", "storage_size")
        self.add_entry("memory_usage_step", "clock_step", "storage_size")
        self.add_entry("storage_changed", "simulation_time", "storage_size")
        self.add_entry("memory_peak", "sim_time", "memory_usage")

        storage = self.process.storage
        clock = self.process.clock
        storage.connect("push", self.on_push)
        storage.connect("pop", self.on_pop)
        storage.connect("changed", self.on_changed)
        clock.connect("step", self.on_step)
        clock.connect("time_added", self.on_time_added)

    def on_changed(self, sim_time, storage_time):
        self.put("storage_changed", (sim_time, storage_time))

    def on_push(self, item):
        clock = self.process.clock
        used_memory = clock.process.get_used_memory()
        self.put("push_time", (item.id,
                               clock.get_simulation_time(),
                               used_memory))
        self.put("push_step", (item.id,
                               clock.get_step(),
                               used_memory))

    def on_pop(self, item):
        clock = self.process.clock
        used_memory = clock.process.get_used_memory()
        self.put("pop_time", (item.id,
                              clock.get_simulation_time(), used_memory))
        self.put("pop_step", (item.id,
                              clock.get_step(), used_memory))

    def on_step(self, steps, current_step):
        self.put("memory_usage_step",
                 (steps,
                  self.process.clock.process.get_used_memory()))

    def on_time_added(self, sim_time, time_added):
        clock = self.process.clock
        self.put("memory_usage_time",
                 (sim_time,
                  clock.process.get_used_memory()))


class EdgeMonitor(Monitor):
    def __init__(self, process):
        Monitor.__init__(self, "EdgeMonitor", process)
        self.add_entry("edge_discovered",
                       "simulation_time",
                       "process_id",
                       "edge_time",
                       "edge_label",
                       "source_node_id",
                       "target_node_id")
        self.add_entry("edge_calculated",
                       "simulation_time",
                       "process_id",
                       "edge_time",
                       "edge_label",
                       "source_node_id",
                       "target_node_id")
        self.add_entry("edges_discovered_time",
                       "simulation_time",
                       "edges_count")
        self.add_entry("edges_calculated_time",
                       "simulation_time",
                       "edges_count")

        self.process.connect("edge_discovered", self.on_edge_discovered)
        self.process.connect("edge_calculated", self.on_edge_calculated)
        self.discovered_edges = 0
        self.calculated_edges = 0

    def on_edge_discovered_in_time(self, sim_time):
        self.put("edges_discovered_time", (sim_time, self.discovered_edges))

    def on_edge_calculated_in_time(self, sim_time):
        self.put("edges_calculated_time", (sim_time, self.calculated_edges))

    def on_time_added(self, sim_time, time_added):
        self.on_edge_discovered_in_time(sim_time)
        self.on_edge_calculated_in_time(sim_time)

    def on_edge_discovered(self,
                           sim_time,
                           process_id,
                           edge_time,
                           edge_label,
                           source_node_id,
                           target_node_id):
        self.put("edge_discovered", (sim_time,
                                     process_id,
                                     edge_time,
                                     edge_label,
                                     source_node_id,
                                     target_node_id))
        self.discovered_edges += 1

    def on_edge_calculated(self,
                           sim_time,
                           process_id,
                           edge_time,
                           edge_label,
                           source_node_id,
                           target_node_id):
        self.put("edge_calculated", (sim_time,
                                     process_id,
                                     edge_time,
                                     edge_label,
                                     source_node_id,
                                     target_node_id))
        self.calculated_edges += 1


class ProcessMonitor(Monitor):
    def __init__(self, process):
        Monitor.__init__(self, "ProcessMonitor", process)
        self.add_entry("wait", "simulation_time")
        self.add_entry("notify", "simulation_time")
        self.add_entry("memory_usage", "simulation_time", "memory_size")
        self.process.connect("notify", self.on_notify)
        self.process.connect("wait", self.on_wait)

    def on_notify(self, time):
        self.put("notify", (time,))

    def on_wait(self, time):
        self.put("wait", (time,))

