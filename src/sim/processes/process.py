import simpy
from gui.events import EventSource
from collections import deque
import gobject
import monitor


class ProcessContext():
    def __init__(self, env, monitor_manager, arguments):
        self.env = env
        self.arguments = arguments
        self.monitor_manager = monitor_manager


class Process(EventSource):
    def __init__(self, id, name, ctx):
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
        self.communicator = Communicator(self)
        self.communicator.connect("async_receive", self.on_async_receive)
        mm = ctx.monitor_manager
        mm.register_process_monitor(self.id, monitor.ProcessMonitor(self))
        mm.register_process_monitor(self.id, monitor.ClockMonitor(self))
        mm.register_process_monitor(self.id, monitor.CommunicationMonitor(self))
        mm.register_process_monitor(self.id, monitor.MemoryMonitor(self))

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def is_awake(self):
        return not self._sleep

    def wait(self, sleep_time = None):
        now = self.ctx.env.now
        if sleep_time is not None:
            if sleep_time < 0:
                raise Exception("sleep time can't be smaller then 0")
            self.fire("sleep", now, sleep_time)
            mm = self.ctx.monitor_manager
            gtm = mm.get_monitor("GlobalTimeMonitor")
            time_evt = self.ctx.env.timeout(sleep_time)

            def time_evt_callback(e):
                gtm.add_timeout(self.ctx.env.now, sleep_time, self.id)
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

    def init_monitor_callbacks(self):
        mm = self.ctx.monitor_manager
        mm.add_process_callback("wait", self.id, self)
        mm.add_process_callback("notify", self.id, self)
        mm.add_process_callback("sleep", self.id, self)
        mm.add_process_callback("log", self.id, self)
        mm.add_process_callback("async_receive", self.id, self.communicator)
        mm.add_process_callback("async_send", self.id, self.communicator)
        mm.add_process_callback("receive", self.id, self.communicator)
        mm.add_process_callback("send", self.id, self.communicator)
        mm.add_process_callback("time_stamp", self.id, self.clock)
        mm.add_process_callback("step", self.id, self.clock)
        gtm = mm.get_monitor("GlobalTimeMonitor")
        mm.add_callback("timeout", gtm)

    def post_init(self):
        mm = self.ctx.monitor_manager
        gtm = mm.get_monitor("GlobalTimeMonitor")
        gtm.add_timeout(0, 0, self.id)

    def init(self):
        raise NotImplementedError()

    def get_used_memory(self):
        raise NotImplementedError()

    def run(self):
        raise NotImplementedError()

    def on_async_receive(self, msg):
        raise NotImplementedError()


class GraphProcess(Process):
    NAME = "Unknow"
    DESCRIPTION = "No description"
    ARGUMENTS = {}

    def __init__(self, id, name, ctx):
        Process.__init__(self, id, self.NAME, ctx)
        self.register_event("edge_discovered")
        self.register_event("edge_calculated")
        ctx.monitor_manager.register_process_monitor(id, monitor.EdgeMonitor(self))

    def solve_edge(self, edge):
        gs = self.ctx.graph_stats
        gs.discover_edge(edge, self)
        self.fire("edge_discovered",
                  self.ctx.env.now,
                  self.id,
                  edge.get_time(),
                  edge.get_label(),
                  edge.get_source().get_id(),
                  edge.get_target().get_id())

        def edge_gen():
            yield self.wait(edge.get_time())
            gs.calculate_edge(edge, self)
            self.fire("edge_calculated",
                      self.ctx.env.now,
                      self.id,
                      edge.get_time(),
                      edge.get_label(),
                      edge.get_source().get_id(),
                      edge.get_target().get_id())

        return self.ctx.env.process(edge_gen())

    def init_monitor_callbacks(self):
        Process.init_monitor_callbacks(self)
        mm = self.ctx.monitor_manager
        mm.add_process_callback("edge_discovered", self.id, self)
        mm.add_process_callback("edge_calculated", self.id, self)


class StorageProcess(GraphProcess):
    def __init__(self, id, name, ctx, storage):
        GraphProcess.__init__(self, id, name, ctx)
        self.storage = storage
        ctx.monitor_manager.register_process_monitor(id, monitor.StorageMonitor(self))

    def get_used_memory(self):
        return self.storage.get_size()

    def notify_storage_change(self):
        self.storage.notify_change()

    def on_async_receive(self, msg):
        self.storage.put_item(msg.data)

    def init_monitor_callbacks(self):
        GraphProcess.init_monitor_callbacks(self)
        mm = self.ctx.monitor_manager
        mm.add_process_callback("push", self.id, self.storage)
        mm.add_process_callback("pop", self.id, self.storage)
        mm.add_process_callback("changed", self.id, self.storage)


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
        self.register_event("async_send")
        self.register_event("async_receive")
        self.process = process
        self._msg_store = simpy.FilterStore(process.ctx.env)
        self.rec = True

    def async_send(self, data, target, tag = None, size = 1):
        ctx = self.process.ctx
        id = self.process.id
        msg = Message(data, self.process.id, target, tag, size)
        self.fire("async_send", msg)
        target_process = ctx.processes[target]
        target_process.communicator._ireceive(msg)
        target_process.notify()

    def _ireceive(self, data):
        self.fire("async_receive", data)

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

        target_process = ctx.processes[target]
        com = target_process.communicator
        evt = com._msg_store.put(Message(data, self.process.id, target, tag, size))
        if evt.triggered:
            self.fire("send", evt.item)
        return evt

    def receive(self, target, tag = None):
        ctx = self.process.ctx
        if target < 0 or target >= len(ctx.processes):
            raise Exception("Unknown source for receive message")

        def match(msg):
            return self._check_msg(msg.source, msg.tag, target, tag)

        evt = self._msg_store.get(match)
        if evt.triggered:
            self.fire("receive", evt.value)
        else:
            evt.callbacks.append(lambda e: self.fire("receive", evt.value))
        return evt

    def receive_now(self, target, tag = None):
        ctx = self.process.ctx
        if target < 0 or target >= len(ctx.processes):
            raise Exception("Unknown source for receive message")

        def match(msg):
            return self._check_msg(msg.source, msg.tag, target, tag)

        evt = self._msg_store.get(match)
        if evt.triggered:
            return evt.value
        else:
            return None

    def get_n_messages(self):
        return len(self._msg_store.items)


class Clock(EventSource):
    def __init__(self, process):
        EventSource.__init__(self)
        self.register_event("time_stamp")
        self.register_event("step")
        self.process = process
        self.time = 0
        self.steps = 0

    def wait(self, time):
        self.fire("time_stamp", self.time, time)
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
    def __init__(self, process):
        EventSource.__init__(self)
        self.register_event("changed")
        self.register_event("push")
        self.register_event("pop")
        self.process = process
        self.peak = 0

    def put(self, value):
        sim_time = self.process.clock.get_simulation_time()
        self.put_item(value)
        self.fire("push", sim_time, self.get_size())
        self.fire("changed",
                  sim_time,
                  self.get_size())
        if self.get_size() > self.peak:
            self.peak = self.get_size()

    def get(self):
        sim_time = self.process.clock.get_simulation_time()
        item = self.get_item()
        self.fire("pop", sim_time, self.get_size())
        self.fire("changed",
                  sim_time,
                  self.get_size())
        return item

    def get_memory_peak(self):
        return self.peak

    def get_size(self):
        raise NotImplementedError()

    def get_item(self):
        raise NotImplementedError()

    def put_item(self, value):
        raise NotImplementedError()


class QueueStorage(Storage):
    def __init__(self, process):
        Storage.__init__(self, process)
        self.container = deque()

    def put_item(self, val):
        self.container.append(val)

    def get_item(self):
        return self.container.popleft()

    def get_size(self):
        return len(self.container)


class StackStorage(Storage):
    def __init__(self, process):
        Storage.__init__(self, process)
        self.container = []

    def put_item(self, val):
        self.container.append(val)

    def get_item(self):
        return self.container.pop()

    def get_size(self):
        return len(self.container)

