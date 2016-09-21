import simpy
from gui.events import EventSource


class ProcessContext():
    def __init__(self, env, monitor_manager, arguments):
        self.env = env
        self.arguments = arguments
        self.monitor_manager = monitor_manager
        self._msg_store = simpy.FilterStore(env)


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
        self.communicator.connect("ireceive", self.on_ireceive)

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def is_awake(self):
        return not self._sleep

    def init(self):
        pass

    def get_used_memory(self):
        return 0

    def get_memory_peak(self):
        return 0

    def run(self):
        return
        yield

    def wait(self, sleep_time = None):
        now = self.ctx.env.now
        if sleep_time is not None:
            if sleep_time < 0:
                raise Exception("sleep time can't be smaller then 0")

            self.fire("sleep", now, sleep_time)

            def time_process():
                time_evt = self.ctx.env.timeout(sleep_time)
                time_evt.callbacks.append(lambda e: self.clock.fire("global_time_added",
                                                                    self.ctx.env.now,
                                                                    sleep_time))
                yield time_evt
                self.clock.wait(sleep_time)

            return self.ctx.env.process(time_process())

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
        self.fire("log", message, msg_tag)

    def on_ireceive(self, data):
        pass

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


class GraphProcess(Process):
    NAME = "Unknow"
    DESCRIPTION = "No description"
    ARGUMENTS = {}

    def __init__(self, id, name, ctx):
        Process.__init__(self, id, self.NAME, ctx)
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


class StorageProcess(GraphProcess):
    NAME = "Storage process"
    DESCRIPTION = "Process with internal storage"
    ARGUMENTS = {}

    def __init__(self, id, name, ctx, storage):
        GraphProcess.__init__(self, id, self.NAME, ctx)
        self.storage = storage

    def get_used_memory(self):
        return self.storage.get_size()

    def get_memory_peak(self):
        return self.storage.get_max_size()

    def on_ireceive(self, data):
        self.storage.put(data.data)

    def init_monitor(self):
        GraphProcess.init_monitor(self)
        mm = self.ctx.monitor_manager
        mm.add_process_callback("push", self.id, self.storage)
        mm.add_process_callback("pop", self.id, self.storage)
        mm.add_process_callback("size_exceeded", self.id, self.storage)


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

        def put_process():
            evt = ctx._msg_store.put(Message(data, self.process.id, target, tag, size))
            if evt.triggered:
                self.fire("send", evt.item)
            yield evt
        return ctx.env.process(put_process())

    def receive(self, target, tag = None):
        ctx = self.process.ctx
        if target < 0 or target >= len(ctx.processes):
            raise Exception("Unknown source for receive message")

        def match(msg):
            return self._check_msg(msg.source, msg.tag, target, tag)

        def get_process():
            evt = ctx._msg_store.get(match)
            if evt.triggered:
                self.fire("receive", evt.value)
            yield evt

        return ctx.env.process(get_process())

    def get_waiting_messages_count(self):
        return len(self.process.ctx._msg_store.items)


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

