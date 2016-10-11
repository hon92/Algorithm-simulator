import re
from src.gui.events import EventSource


class MonitorManager():

    REGEX = "(^p)(\d+)(_)(\w+)"

    def __init__(self):
        self.monitors = {}
        self.listeners = {}
        self.process_listeners = {}
        self.global_monitors = {}

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

    def register_monitor(self, monitor):
        m = self.global_monitors.get(monitor.get_id())
        if m:
            raise Exception("Cant register more same global monitors")
        self.global_monitors[monitor.get_id()] = monitor

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
        self.global_monitors = {}

    def get_monitor(self, monitor_id):
        return self.global_monitors.get(monitor_id)

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


class MonitorBase(EventSource):
    def __init__(self, id):
        EventSource.__init__(self)
        self.register_event("entry_put")
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
                self.fire("entry_put", val)
            else:
                raise Exception("Invalid arguments for entry '" + entry_name + "'")
        else:
            raise Exception("Unknown entry name")

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


class Monitor(MonitorBase):
    def __init__(self, id, process):
        MonitorBase.__init__(self, id)
        self.process = process


class ClockMonitor(Monitor):
    def __init__(self, process):
        Monitor.__init__(self, "ClockMonitor", process)
        self.add_entry("time_stamp",
                       "time",
                       "time_added")
        self.add_entry("step",
                       "previous_steps",
                       "steps")
        process.clock.connect("time_stamp", self.on_time_stamp)
        process.clock.connect("step", self.on_step)

    def on_time_stamp(self, time, time_added):
        self.put("time_stamp", (time, time_added))

    def on_step(self, prev_steps, steps):
        self.put("step", (prev_steps, steps))


class MemoryMonitor(Monitor):
    def __init__(self, process):
        Monitor.__init__(self, "MemoryMonitor", process)
        self.add_entry("memory_usage", "simulation_time", "memory_usage")
        gtm = process.ctx.monitor_manager.get_monitor("GlobalTimeMonitor")
        gtm.connect("timeout", self.on_timeout)

    def on_timeout(self, sim_time, time, process_id):
        self.put("memory_usage", (sim_time,
                                  self.process.get_used_memory()))


class StorageMonitor(Monitor):
    def __init__(self, process):
        Monitor.__init__(self, "StorageMonitor", process)
        self.add_entry("changed",
                       "simulation_time",
                       "size")
        self.add_entry("push",
                       "simulation_time",
                       "storage_size")
        self.add_entry("pop",
                       "simulation_time",
                       "storage_size")
        self.process.storage.connect("changed",
                                     self.on_storage_changed)
        process.storage.connect("push", self.on_push)
        process.storage.connect("pop", self.on_pop)

    def on_storage_changed(self, sim_time, size):
        self.put("changed", (sim_time, size))

    def on_push(self, sim_time, storage_size):
        self.put("push", (sim_time, storage_size))

    def on_pop(self, sim_time, storage_size):
        self.put("pop", (sim_time, storage_size))


class ProcessMonitor(Monitor):
    def __init__(self, process):
        Monitor.__init__(self, "ProcessMonitor", process)
        self.add_entry("wait",
                       "simulation_time")
        self.add_entry("notify",
                       "simulation_time")
        self.add_entry("sleep",
                       "simulation_time",
                       "sleep_time")
        process.connect("wait", self.on_wait)
        process.connect("sleep", self.on_sleep)
        process.connect("notify", self.on_notify)

    def on_wait(self, sim_time):
        self.put("wait", (sim_time,))

    def on_sleep(self, sim_time, sleep_time):
        self.put("sleep", (sim_time, sleep_time))

    def on_notify(self, sim_time):
        self.put("notify", (sim_time,))


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
        self.add_entry("edges_discovered_in_time",
                       "simulation_time",
                       "count")
        self.add_entry("edges_discovered_cummulative",
                       "simulation_time",
                       "cummulative_sum")

        self.edges_discovered = 0
        self.edges_time_sum = 0
        mm = process.ctx.monitor_manager
        gtm = mm.get_monitor("GlobalTimeMonitor")
        gtm.connect("timeout", self.on_timeout)
        self.process.connect("edge_discovered", self.on_edge_discovered)
        self.process.connect("edge_calculated", self.on_edge_calculated)

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
        self.edges_discovered += 1

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
        self.edges_time_sum += edge_time

    def on_timeout(self, sim_time, time, process_id):
        self.put("edges_discovered_in_time", (sim_time, self.edges_discovered))
        self.put("edges_discovered_cummulative", (sim_time, self.edges_time_sum))


class CommunicationMonitor(Monitor):
    def __init__(self, process):
        Monitor.__init__(self, "CommunicationMonitor", process)
        self.add_entry("send",
                       "simulation_time",
                       "target_process_id",
                       "size")
        self.add_entry("receive",
                       "simulation_time",
                       "source_process_id",
                       "size")
        self.add_entry("async_send",
                       "simulation_time",
                       "target_process_id",
                       "size")
        self.add_entry("async_receive",
                       "simulation_time",
                       "source_process_id",
                       "size")
        process.communicator.connect("send", self.on_send)
        process.communicator.connect("receive", self.on_receive)
        process.communicator.connect("async_send", self.on_async_send)
        process.communicator.connect("async_receive", self.on_async_receive)

    def on_send(self, msg):
        self.put("send",
                 (self.process.clock.get_simulation_time(),
                  msg.target,
                  msg.size))

    def on_receive(self, msg):
        self.put("receive",
                 (self.process.clock.get_simulation_time(),
                  msg.source,
                  msg.size))

    def on_async_send(self, msg):
        self.put("async_send",
                 (self.process.clock.get_simulation_time(),
                  msg.target,
                  msg.size))

    def on_async_receive(self, msg):
        self.put("async_receive",
                 (self.process.clock.get_simulation_time(),
                  msg.source,
                  msg.size))


class GlobalTimeMonitor(MonitorBase):
    def __init__(self):
        MonitorBase.__init__(self, "GlobalTimeMonitor")
        self.register_event("timeout")
        self.add_entry("timeout",
                       "simulation_time",
                       "time",
                       "process_id")

    def add_timeout(self, sim_time, time, process_id):
        val = (sim_time, time, process_id)
        self.put("timeout", val)
        self.fire("timeout", *val)


class GlobalMemoryMonitor(MonitorBase):
    def __init__(self, global_time_monitor, processes):
        MonitorBase.__init__(self, "GlobalMemoryMonitor")
        self.add_entry("memory_usage",
                       "simulation_time",
                       "memory_usage")
        self.processes = processes
        global_time_monitor.connect("timeout", self.on_timeout)

    def on_timeout(self, sim_time, time, process_id):
        mem_usage = 0
        for p in self.processes:
            mem_usage += p.get_used_memory()
        self.put("memory_usage", (sim_time, mem_usage))


class GlobalStorageMonitor(MonitorBase):
    def __init__(self, processes):
        MonitorBase.__init__(self, "GlobalStorageMonitor")
        self.add_entry("changed",
                       "simulation_time",
                       "storage_size")
        self.processes = processes
        for p in processes:
            p.storage.connect("changed", self.on_storage_changed)

    def on_storage_changed(self, sim_time, size):
        s = 0
        for p in self.processes:
            s += p.get_used_memory()
        self.put("changed", (sim_time, s))

