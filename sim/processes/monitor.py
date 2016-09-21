import re


class MonitorManager():
    REGEX = "(^p)(\d+)(_)(\w+)"

    def __init__(self):
        self.monitors = {}
        self.events = {} #key -> event name, value -> callbacks list
        self.process_monitors = {} # key -> process id, val -> callbacks list

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
# 
#     def collect(self, monitors_to_collect = None):
#         for mon in self.monitors:
#             yield mon.collect(monitors_to_collect)
 
    def get_process_monitor(self, pid, monitor_name):
        if pid in self.monitors:
            monitors = self.monitors[pid]
            for m in monitors:
                if m.get_id() == monitor_name:
                    return m
        return None


class Entry():
    def __init__(self, entry_name, args):
        self.entry_name = entry_name
        self.args = args

    def check(self, val):
        return len(val) == len(self.args)


class Monitor():
    def __init__(self, id):
        self.id = id
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

    def get_header_data(self):
        return ";".join(self.data.keys())


class TimeMonitor(Monitor):
    def __init__(self, clock):
        Monitor.__init__(self, "TimeMonitor")
        self.add_entry("time_added", "current_time", "added_time")
        self.clock = clock
        self.clock.connect("time_added", self.on_time_added)

    def on_time_added(self, current_time, added_time):
        self.put("time_added", (current_time, added_time))


class MemoryMonitor(Monitor):
    def __init__(self, storage, clock):
        Monitor.__init__(self, "MemoryMonitor")
        self.add_entry("push_time", "item", "simulation_time", "storage_size")
        self.add_entry("pop_time", "item", "simulation_time", "storage_size")
        self.add_entry("push_step", "item", "clock_step", "storage_size")
        self.add_entry("pop_step", "item", "clock_step", "storage_size")
        self.add_entry("memory_usage_time", "simulation_time", "storage_size")
        self.add_entry("memory_usage_step", "clock_step", "storage_size")
        self.storage = storage
        self.clock = clock
        self.storage.connect("push", self.on_push)
        self.storage.connect("pop", self.on_pop)
        self.clock.connect("step", self.on_step)

    def on_push(self, item):
        used_memory = self.clock.process.get_used_memory()
        self.put("push_time", (item,
                               self.clock.get_simulation_time(),
                               used_memory))
        self.put("push_step", (item,
                               self.clock.get_step(),
                               used_memory))

    def on_pop(self, item):
        used_memory = self.clock.process.get_used_memory()
        self.put("pop_time", (item,
                              self.clock.get_simulation_time(), used_memory))
        self.put("pop_step", (item,
                              self.clock.get_step(), used_memory))

    def on_step(self, steps, current_step):
        self.put("memory_usage_time",
                 (self.clock.get_simulation_time(),
                  self.clock.process.get_used_memory()))
        self.put("memory_usage_step",
                 (steps,
                  self.clock.process.get_used_memory()))


class EdgeMonitor(Monitor):
    def __init__(self, graph_process):
        Monitor.__init__(self, "EdgeMonitor")
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
        graph_process.connect("edge_discovered", self.on_edge_discovered)
        graph_process.connect("edge_calculated", self.on_edge_calculated)

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

