import simpy
from gui.events import EventSource
from collections import deque
import gobject


class ProcessContext():
    def __init__(self, env, monitor_manager, arguments):
        self.env = env
        self.arguments = arguments
        self.monitor_manager = monitor_manager


class Process(EventSource):
    def __init__(self, id, name, ctx, storage):
        EventSource.__init__(self)
        self.register_event("wait")
        self.register_event("notify")
        self.register_event("sleep")
        self.register_event("log")
        self._sleep = False
        self.id = id
        self.name = name
        self.ctx = ctx
        self.block_event = ctx.env.event()
        self.clock = Clock(self)
        self.storage = storage
        self.storage.set_process(self)
        self.communicator = Communicator(self)
        self.communicator.connect("ireceive", self.on_ireceive)

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def is_awake(self):
        return not self._sleep

    def pre_init(self):
        mm = self.ctx.monitor_manager
        mem_monitor = mm.get_process_monitor(self.id, "MemoryMonitor")
        edge_monitor = mm.get_process_monitor(self.id, "EdgeMonitor")
        if edge_monitor:
            mm.connect("global_time_added", lambda s, t: edge_monitor.on_time_added(s, t))

        if mem_monitor:
            if self.id == 0:
                def put_memory_peak(sim_time, time_added):
                    mp = 0
                    for p in self.ctx.processes:
                        mp += p.get_used_memory()
                    mem_monitor.put("memory_peak", (sim_time, mp))
                mm.connect("changed", put_memory_peak)

        self.clock.fire("global_time_added",
                        self.clock.get_simulation_time(),
                        0)

    def init(self):
        pass

    def get_used_memory(self):
        return self.storage.get_size()

    def get_memory_peak(self):
        return self.storage.get_memory_peak()

    def run(self):
        return
        yield

    def wait(self, sleep_time = None):
        now = self.ctx.env.now
        if sleep_time is not None:
            if sleep_time < 0:
                raise Exception("sleep time can't be smaller then 0")
            self.fire("sleep", now, sleep_time)
            time_evt = self.ctx.env.timeout(sleep_time)
            def time_evt_callback(e):
                self.clock.fire("global_time_added",
                                self.ctx.env.now,
                                sleep_time)
                self.clock.wait(sleep_time)
            time_evt.callbacks.append(time_evt_callback)
            return time_evt
        else:
            self.fire("wait", now)
            self._sleep = True
            return self.block_event

    def notify(self, val = None):
        if self._sleep:
            self.block_event.succeed(val)
            self.block_event = self.ctx.env.event()
            self._sleep = False
            self.fire("notify", self.ctx.env.now)

    def log(self, message, msg_tag = "out"):
        gobject.idle_add(self.fire, "log", message, msg_tag, priority = gobject.PRIORITY_HIGH)

    def on_ireceive(self, msg):
        self.storage.put(msg.data)

    def init_monitor(self):
        mm = self.ctx.monitor_manager
        mm.add_process_callback("wait", self.id, self)
        mm.add_process_callback("notify", self.id, self)
        mm.add_process_callback("sleep", self.id, self)
        mm.add_process_callback("log", self.id, self)
        mm.add_process_callback("ireceive", self.id, self.communicator)
        mm.add_process_callback("isend", self.id, self.communicator)
        mm.add_process_callback("receive", self.id, self.communicator)
        mm.add_process_callback("send", self.id, self.communicator)
        mm.add_process_callback("time_added", self.id, self.clock)
        mm.add_process_callback("step", self.id, self.clock)
        mm.add_callback("global_time_added", self.clock)
        mm.add_callback("step", self.clock)
        mm.add_callback("changed", self.storage)
        mm.add_process_callback("push", self.id, self.storage)
        mm.add_process_callback("pop", self.id, self.storage)
        mm.add_process_callback("size_exceeded", self.id, self.storage)

    def notify_storage_change(self):
        self.storage.notify_change()


class GraphProcess(Process):
    NAME = "Unknow"
    DESCRIPTION = "No description"
    ARGUMENTS = {}

    def __init__(self, id, name, ctx, storage):
        Process.__init__(self, id, self.NAME, ctx, storage)
        self.register_event("edge_discovered")
        self.register_event("edge_calculated")

    def solve_edge(self, edge):
        gs = self.ctx.graph_stats
        gs.discover_edge(edge.source.id,
                         edge.target.id,
                         edge.label,
                         self.id)
        self.fire("edge_discovered",
                  self.ctx.env.now,
                  self.id,
                  edge.get_time(),
                  edge.get_label(),
                  edge.get_source().get_id(),
                  edge.get_target().get_id())

        def edge_gen():
            yield self.wait(edge.get_time())
            gs.calculate_edge(edge.source.id,
                              edge.target.id,
                              edge.label,
                              self.id)
            self.fire("edge_calculated",
                      self.ctx.env.now,
                      self.id,
                      edge.get_time(),
                      edge.get_label(),
                      edge.get_source().get_id(),
                      edge.get_target().get_id())

        return self.ctx.env.process(edge_gen())

    def init_monitor(self):
        Process.init_monitor(self)
        mm = self.ctx.monitor_manager
        mm.add_process_callback("edge_discovered", self.id, self)
        mm.add_process_callback("edge_calculated", self.id, self)


class Message():
    def __init__(self, data, source, target, tag, size):
        self.data = data
        self.target = target
        self.source = source
        self.tag = tag
        self.size = size


class Communicator(EventSource):
    def __init__(self, process):
        EventSource.__init__(self)
        self.register_event("send")
        self.register_event("receive")
        self.register_event("isend")
        self.register_event("ireceive")
        self.process = process
        self._msg_store = simpy.FilterStore(process.ctx.env)

    def isend(self, data, target, tag = None, size = 1):
        ctx = self.process.ctx
        id = self.process.id
        msg = Message(data, self.process.id, target, tag, size)
        self.fire("isend", msg)
        target_process = ctx.processes[target]
        target_process.communicator._ireceive(msg)
        target_process.notify()

    def _ireceive(self, data):
        self.fire("ireceive", data)

    def _check_msg(self, m_source, m_tag, target, tag):
        if m_source == target:
            if tag is not None:
                return m_tag == tag
            return True
        return False

    def send(self, data, target, tag = None, size = 1):
        ctx = self.process.ctx
        if target < 0 or target >= len(ctx.processes):
            raise Exception("Unknown target for message send")

        evt = self._msg_store.put(Message(data, self.process.id, target, tag, size))
        if evt.triggered:
            self.fire("send", evt.item)
        return evt

    def receive(self, target, tag = None):
        ctx = self.process.ctx
        if target < 0 or target >= len(ctx.processes):
            raise Exception("Unknown source for receive message")

        def match(msg):
            return self._check_msg(msg.source, msg.tag, target, tag)

        target_process = ctx.processes[target]
        com = target_process.communicator
        evt = com._msg_store.get(match)
        if evt.triggered:
            self.fire("receive", evt.value)
        return evt

    def get_n_messages(self):
        return len(self._msg_store.items)


class Clock(EventSource):
    def __init__(self, process):
        EventSource.__init__(self)
        self.register_event("global_time_added")
        self.register_event("time_added")
        self.register_event("step")
        self.process = process
        self.time = 0
        self.steps = 0

    def wait(self, time):
        self.fire("time_added", self.time, time)
        self.time += time

    def tick(self):
        self.fire("step", self.steps, self.steps + 1)
        self.steps += 1

    def get_time(self):
        return self.time

    def get_step(self):
        return self.steps

    def get_simulation_time(self):
        return self.process.ctx.env.now

    def get_waiting_time(self):
        return self.get_simulation_time() - self.get_time()


class Storage(EventSource):
    def __init__(self):
        EventSource.__init__(self)
        self.register_event("changed")
        self.register_event("push")
        self.register_event("pop")
        self.register_event("size_exceeded")
        self.process = None
        self.peak = 0
        self.connect("changed", self._check_mem_peak)

    def set_process(self, process):
        self.process = process

    def notify_change(self):
        self.fire("changed",
                  self.process.clock.get_simulation_time(),
                  self.get_size())

    def _check_mem_peak(self, sim_time, mem_size):
        if mem_size > self.peak:
            self.peak = mem_size
            self.fire("size_exceeded", sim_time, self.peak)

    def put(self, value):
        self.put_item(value)
        self.fire("push", value)
        self.notify_change()

    def get(self):
        item = self.get_item()
        self.fire("pop", item)
        self.notify_change()
        return item

    def get_size(self):
        pass

    def get_item(self):
        pass

    def put_item(self, value):
        pass

    def get_memory_peak(self):
        return self.peak


class QueueStorage(Storage):
    def __init__(self):
        Storage.__init__(self)
        self.container = deque()

    def put_item(self, val):
        self.container.append(val)

    def get_item(self):
        return self.container.popleft()

    def get_size(self):
        return len(self.container)


class StackStorage(Storage):
    def __init__(self):
        Storage.__init__(self)
        self.container = []

    def put_item(self, val):
        self.container.append(val)

    def get_item(self):
        return self.container.pop()

    def get_size(self):
        return len(self.container)

