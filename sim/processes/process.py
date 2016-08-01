from gui.events import EventSource
from storage import Storage
from sim.processes.monitor import MonitorManager

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

class Comunicator(EventSource):
    def __init__(self):
        EventSource.__init__(self)
        self.register_event("send")
        self.register_event("receive")
        self.processes = []

    def get_processes(self):
        return self.processes

    def set_processes(self, processes):
        self.processes = processes

    def send(self, node, process):
        self.fire("receive", node, process.get_id())
        process.comunicator.receive(node, process)

    def receive(self, node, process):
        self.fire("send", node, process.get_id())
        process.storage.put(node)

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
        self.clock = Clock(self)
        self.storage = Storage()
        self.comunicator = Comunicator()
        self.monitor_manager = MonitorManager()

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def initialize(self):
        pass

    def run(self):
        yield None

    def wait(self, sleep_time = None):
        if sleep_time:
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

    def notify(self):
        if self._sleep:
            self.block_event.succeed()
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

    def get_monitor_manager(self):
        return self.monitor_manager

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

    def set_processes(self, processes):
        self.comunicator.set_processes(processes)
