from gui.events import EventSource
from storage import Storage

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
        self.communicator = Communicator(self)
        self.communicator.connect("receive", self.on_message_receive)

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def is_awake(self):
        return not self._sleep

    def init(self):
        pass

    def get_used_memory(self):
        pass

    def run(self):
        return
        yield

    def wait(self, sleep_time = None):
        if sleep_time is not None:
            if sleep_time < 0:
                raise Exception("sleep time can't be smaller then 0")

            now = self.ctx.env.now
            self.fire("sleep", now, sleep_time)

            def time_process():
                yield self.ctx.env.timeout(sleep_time)
                self.clock.wait(sleep_time)

            return self.ctx.env.process(time_process())

        else:
            self.fire("wait", self.ctx.env.now)
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

    def on_message_receive(self, message, source_id):
        print message

class GraphProcess(Process):
    NAME = "Unknow"
    DESCRIPTION = "No description"
    ARGUMENTS = {}

    def __init__(self, id, name, ctx):
        Process.__init__(self, id, self.NAME, ctx)
        self.register_event("edge_discovered")
        self.register_event("edge_calculated")

        self.clock = Clock(self)
        self.storage = Storage()
        self.communicator = Communicator(self)

    def solve_edge(self, edge):
        self.discover_edge(edge)

        def edge_gen():
            yield self.wait(edge.get_time())
            self.complete_edge(edge)

        return self.env.process(edge_gen())

    def discover_edge(self, edge):
        edge.discover(self.id)
        self.fire("edge_discovered",
                  self.env.now, # simulation time
                  self.clock.get_time(), # process time
                  self.clock.get_step() # process step
                 )

    def complete_edge(self, edge):
        edge.complete(self.id)
        self.fire("edge_calculated",
                  self.env.now,
                  self.clock.get_time(),
                  self.clock.get_step(),
                  edge.get_time())

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
        self.process = process

    def send_node(self, node, target_process_id):
        ctx = self.process.ctx
        id = self.process.id
        self.fire("send", node, id)
        target_process = ctx.processes[target_process_id]
        target_process.communicator.receive_node(node, id)
        #process.communicator.receive_node(node, self.process.id)
        target_process.notify()

    def receive_node(self, node, source_process_id):
        self.fire("receive", node, source_process_id)
        #self.fire("send", node, source_process_id)
        #self.process.storage.put(node)
        pass

    def get_processes_count(self):
        return len(self.process.ctx.processes)

    def send(self, data, target, tag = None, size = 1):
        ctx = self.process.ctx
        if target < 0 or target >= len(ctx.processes):
            raise Exception("Unknown target for message send")
        return ctx._msg_store.put(Message(data, self.process.id, target, tag, size))

    def receive(self, target, tag = None):
        ctx = self.process.ctx
        if target < 0 or target >= len(ctx.processes):
            raise Exception("Unknown source for receive message")

        def match(msg):
            return self._check_message(msg.source, msg.tag, target, tag)

        return ctx._msg_store.get(match)

    def get_waiting_messages(self):
        return len(self.process.ctx._msg_store.items)


class Clock(EventSource):
    def __init__(self, process):
        EventSource.__init__(self)
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

        """
        mm = self.process.get_monitor_manager()
        mem_monitor = mm.get_monitor("MemoryMonitor")
        mem_monitor.put("memory_usage_time",
                        (self.process.env.now,
                         self.process.storage.get_size())
                        )
        mem_monitor.put("memory_usage_step",
                        (self.steps,
                         self.process.storage.get_size())
                        )
        """

    def get_time(self):
        return self.time

    def get_step(self):
        return self.steps

    def get_simulation_time(self):
        return self.process.env.now



import simpy
class WorldCommunicator(EventSource):
    def __init__(self, processes):
        EventSource.__init__(self)
        self.processes = processes
        self.store = simpy.FilterStore(processes[0].env)

    def get_process_count(self):
        return len(self.processes)

    def _check_message(self, m_source, m_tag, target, tag):
        if m_source == target:
            if tag is not None:
                return m_tag == tag
            return True
        return False

    def send(self, data, source, target, tag):
        if target < 0 or target >= len(self.processes):
            raise Exception("Unknown target for message send")

        return self.store.put(Message(data, source, target, tag))

    def receive(self, source, target, tag):
        if source < 0 or source >= len(self.processes):
            raise Exception("Unknown source for receive message")

        def match(msg):
            return self._check_message(msg.source, msg.tag, target, tag)

        return self.store.get(match)

    def get_messages_count(self):
        return len(self.store.items)


