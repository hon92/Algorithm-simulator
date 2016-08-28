from gui.events import EventSource
from storage import Storage
from sim.processes.monitor import MonitorManager
from collections import deque

class Clock(EventSource):
    def __init__(self, process):
        EventSource.__init__(self)
        self.register_event("wait")
        self.register_event("step")
        self.process = process
        self.time = 0
        self.steps = 0

    def wait(self, time):
        self.fire("wait", self.time, time)
        self.time += time

    def tick(self):
        self.fire("step", self.steps, self.steps + 1)
        self.steps += 1
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

    def get_time(self):
        return self.time

    def get_step(self):
        return self.steps

    def get_simulation_time(self):
        return self.process.env.now

class Message():
    def __init__(self, data, source, target, tag):
        self.data = data
        self.target = target
        self.source = source
        self.tag = tag

class WorldComunicator(EventSource):
    def __init__(self, processes):
        EventSource.__init__(self)
        self.processes = processes
        self.pending_messages = []
        self.waiting_messages = []
        self.waiting_callbacks = {}

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

        for sl in self.waiting_messages:
            s, tg = sl
            if self._check_message(s, tg, target, tag):
                source_process = self.processes[source]
                evt = source_process.env.event()
                evt.succeed()
                target_process = self.processes[target]
                target_process.notify(data)
                self.waiting_messages.remove(sl)
                return evt

        msg = Message(data, source, target, tag)
        self.pending_messages.append(msg)
        source_process = self.processes[source]
        return source_process.wait()

    def receive(self, source, target, tag):
        if source < 0 or source >= len(self.processes):
            raise Exception("Unknown source for receive message")

        for msg in self.pending_messages:
            if self._check_message(msg.source, msg.tag, target, tag):
                source_process = self.processes[msg.source]
                source_process.notify()
                self.pending_messages.remove(msg)
                target_process = self.processes[target]
                evt = target_process.env.event()
                evt.succeed(msg.data)
                return evt

        self.waiting_messages.append((source, tag))
        source_process = self.processes[source]
        return source_process.wait()

class Comunicator(EventSource):
    def __init__(self, process):
        EventSource.__init__(self)
        self.register_event("send")
        self.register_event("receive")
        self.world_com = None
        self.process = process

    def get_processes(self):
        return self.world_com.processes

    def get_process_count(self):
        return self.world_com.get_process_count()

    def send_node(self, node, target_process_id):
        self.fire("receive", node, target_process_id)
        process = self.world_com.processes[target_process_id]
        process.comunicator.receive_node(node, self.process.id)
        process.notify()

    def receive_node(self, node, source_process_id):
        self.fire("send", node, source_process_id)
        self.process.storage.put(node)

    def get_count(self):
        return len(self.processes)

    def send(self, data, target, tag = None):
        return self.world_com.send(data, self.process.id, target, tag)

    def receive(self, target, tag = None):
        return self.world_com.receive(self.process.id, target, tag)

    def set_world_comunicator(self, world_com):
        self.world_com = world_com

class Process(EventSource):
    def __init__(self, id, name, env):
        EventSource.__init__(self)
        self.register_event("wait")
        self.register_event("notify")
        self.register_event("sleep")
        self.register_event("log")
        self._sleep = False
        self.id = id
        self.name = name
        self.env = env
        self.block_event = env.event()

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def initialize(self):
        pass

    def run(self):
        yield None

    def wait(self, sleep_time = None):
        if sleep_time is not None:
            now = self.env.now
            self.fire("sleep", now, sleep_time)

            def time_process():
                yield self.env.timeout(sleep_time)
                self.clock.wait(sleep_time)

            return self.env.process(time_process())

        else:
            self.fire("wait", self.env.now)
            self._sleep = True
            return self.block_event

    def notify(self, val = None):
        if self._sleep:
            self.block_event.succeed(val)
            self.block_event = self.env.event()
            self._sleep = False
            self.fire("notify", self.env.now)

    def log(self, message, msg_tag = "out"):
        self.fire("log", message, msg_tag)

class GraphProcess(Process):
    NAME = "Unknow"
    DESCRIPTION = "No description"

    def __init__(self, id, name, env, graph):
        Process.__init__(self, id, name, env)
        self.register_event("edge_discovered")
        self.register_event("edge_calculated")
        self.register_event("edge_completed")
        self.graph = graph
        self.clock = Clock(self)
        self.storage = Storage()
        self.comunicator = Comunicator(self)
        self.monitor_manager = MonitorManager()

    def get_monitor_manager(self):
        return self.monitor_manager

    def get_world_comunicator(self):
        return self.comunicator.world_com

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
        self.fire("edge_completed",
                  self.env.now,
                  self.clock.get_time(),
                  self.clock.get_step(),
                 )
        self.fire("edge_calculated",
                  self.env.now,
                  self.clock.get_time(),
                  self.clock.get_step(),
                  edge.get_time())
