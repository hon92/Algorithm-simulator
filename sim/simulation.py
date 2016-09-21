import simpy
from gui import events
from sim.processes.process import ProcessContext
from sim.processes.monitor import MonitorManager
from gui.graphstats import GraphStats, VisualGraphStats


class AbstractSimulation(events.EventSource):
    def __init__(self, process_type, process_count, arguments = None):
        events.EventSource.__init__(self)
        self.register_event("start")
        self.register_event("end")
        self.register_event("stop")
        self.register_event("interrupt")
        self.running = False
        self.process_type = process_type
        self.process_count = process_count
        self.processes_events = []
        monitor_manager = MonitorManager()
        self.ctx = ProcessContext(simpy.Environment(),
                                  monitor_manager,
                                  arguments)

        monitor_manager.add_callback("start", self)
        monitor_manager.add_callback("end", self)
        monitor_manager.add_callback("stop", self)
        monitor_manager.add_callback("interrupt", self)

    def is_running(self):
        return self.running

    def get_process_count(self):
        return self.process_count

    def get_process_type(self):
        return self.process_type

    def _create_procesess(self):
        processes = self.create_processes()
        self.ctx.processes = processes

    def start(self):
        self._create_procesess()
        self.running = True
        self.fire("start", self)
        self._prepare()
        self._run()

    def stop(self):
        if self.is_running():
            self.running = False
            for e in self.processes_events:
                try:
                    e.fail(simpy.core.StopSimulation("Canceled"))
                except Exception:
                    pass
            self.processes_events = []
            self.ctx.processes = []
            self.ctx.env._now = 0

    def _run(self):
        success = self.run()
        self.running = False
        if success:
            self.fire("end", self)

    def _prepare(self):
        self.prepare()
        self.processes_events = []
        for p in self.ctx.processes:
            p.init_monitor()
            p.init()
            e = self.ctx.env.process(p.run())
            self.processes_events.append(e)

    def run(self):
        try:
            error = self.ctx.env.run()
            if error:
                self.fire("stop", error)
                return False
            return True
        except simpy.core.StopSimulation:
            self.fire("stop", error)
            return False
        except Exception as ex:
            self.fire("interrupt", ex.message)
            return False

    def prepare(self):
        pass

    def create_processes(self):
        return []


class Simulation(AbstractSimulation):
    def __init__(self, process_type, process_count, graph, arguments = None):
        AbstractSimulation.__init__(self, process_type, process_count, arguments)
        self.ctx.graph = graph
        self.ctx.graph_stats = GraphStats(graph)

    def prepare(self):
        self.ctx.graph_stats.reset()

    def create_processes(self):
        from processes import algorithms as al
        from processes import monitor
        procesess = []
        for i in xrange(self.get_process_count()):
            process = al.Algorithm1(i, self.ctx)
            id = process.id
            mm = self.ctx.monitor_manager
            mm.register_process_monitor(id, monitor.MemoryMonitor(process.storage,
                                                                  process.clock))
            mm.register_process_monitor(id, monitor.TimeMonitor(process.clock))
            mm.register_process_monitor(id, monitor.ProcessMonitor(process))
            mm.register_process_monitor(id, monitor.EdgeMonitor(process))
            procesess.append(process)
        return procesess


class VisualSimulation(Simulation):
    def __init__(self, process_type, process_count, graph, arguments = None):
        Simulation.__init__(self, process_type, process_count, graph, arguments)
        self.register_event("step")
        self.register_event("visible_step")
        self.generator = None
        self.visible_count = 0
        self.ctx.graph_stats = VisualGraphStats(graph, process_count)

    def prepare(self):
        self.visible_count = 0
        self.generator = self._create_generator()
        self.ctx.graph_stats.reset()

    def step(self):
        try:
            val = next(self.generator)
            self.fire("step", self, val)
            return val
        except StopIteration:
            return None

    def visible_step(self):
        while True:
            val = self.step()
            if val and self.is_new_discovered():
                self.fire("visible_step", self, val)
                return val
            if not val:
                self.fire("visible_step", self, val)
                break

    def is_new_discovered(self):
        curr = self.ctx.graph_stats.get_discovered_nodes_count()
        if curr != self.visible_count:
            self.visible_count = curr
            return True
        return False

    def _create_generator(self):
        try:
            step = 0
            while True:
                self.ctx.env.step()
                step += 1
                yield step
        except simpy.core.EmptySchedule:
            self.fire("end", self)

    def run(self):
        self._create_procesess()
        self.running = True
        self.fire("start", self)
        self._prepare()

