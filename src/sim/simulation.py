import simpy
from gui import events
from sim.processes.process import ProcessContext
from sim.processes.monitor import MonitorManager
from sim.processfactory import process_factory as pf
from gui.graphstats import GraphStats, VisualGraphStats
from processes.monitor import GlobalTimeMonitor, GlobalMemoryMonitor
from sim.processes.process import StorageProcess
from src.sim.processes.monitor import GlobalStorageMonitor


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
        self.arguments = arguments
        self.processes_events = []
        self.ctx = ProcessContext(simpy.Environment(),
                                  MonitorManager(),
                                  arguments)

        self.ctx.monitor_manager.add_callback("start", self)
        self.ctx.monitor_manager.add_callback("end", self)
        self.ctx.monitor_manager.add_callback("stop", self)
        self.ctx.monitor_manager.add_callback("interrupt", self)

    def is_running(self):
        return self.running

    def get_process_count(self):
        return self.process_count

    def get_process_type(self):
        return self.process_type

    def get_arguments(self):
        return self.arguments

    def _create_procesess(self):
        self.ctx.monitor_manager.clear_monitors()
        processes = self.create_processes()
        for p in processes:
            p.init_monitor_callbacks()

        self.ctx.processes = processes

    def start(self):
        self._create_procesess()
        self.running = True
        self._prepare()
        self.fire("start", self)
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
        self.ctx.env._now = 0
        self.prepare()
        self.processes_events = []
        for p in self.ctx.processes:
            p.init()
            p.post_init()
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
    def __init__(self, process_type, process_count, graph,
                 network_model,process_model, arguments = None):
        AbstractSimulation.__init__(self, process_type, process_count, arguments)
        self.ctx.graph = graph
        self.ctx.graph_stats = GraphStats(graph)
        self.ctx.network_model = network_model
        self.ctx.process_model = process_model

    def prepare(self):
        self.ctx.graph_stats.reset()

    def create_processes(self):
        procesess = []
        global_time_monitor = GlobalTimeMonitor()
        mm = self.ctx.monitor_manager
        mm.register_monitor(global_time_monitor)

        for i in xrange(self.get_process_count()):
            procesess.append(pf.create_process(i, self.ctx, self.process_type))

        global_memory_monitor = GlobalMemoryMonitor(global_time_monitor, procesess)
        mm.register_monitor(global_memory_monitor)
        pr = procesess[0]
        if issubclass(pr.__class__, StorageProcess):
            global_storage_monitor = GlobalStorageMonitor(procesess)
            mm.register_monitor(global_storage_monitor)
        return procesess


class VisualSimulation(Simulation):
    def __init__(self, process_type, process_count, graph,
                 network_model, process_model, arguments = None):
        Simulation.__init__(self, process_type, process_count, graph,
                            network_model, process_model, arguments)
        self.register_event("step")
        self.register_event("visible_step")
        self.generator = None
        self.discovered_nodes = 0
        self.calculated_edges = 0
        self.discovered_edges = 0
        self.ctx.graph_stats = VisualGraphStats(graph, process_count)

    def _create_generator(self):
        try:
            step = 0
            while True:
                self.ctx.env.step()
                step += 1
                yield step
        except simpy.core.StopSimulation:
            self.running = False
            self.ctx.env = simpy.Environment()
            self.fire("stop", self)
        except simpy.core.EmptySchedule:
            self.running = False
            self.fire("end", self)
        except Exception as ex:
            self.running = False
            self.ctx.env = simpy.Environment()
            self.fire("interrupt", ex.message)

    def prepare(self):
        self.discovered_nodes = 0
        self.calculated_edges = 0
        self.discovered_edges = 0
        self.ctx.graph_stats.reset()
        self.generator = self._create_generator()

    def do_visible_step(self):
        s = 0
        self.last_sim_time = self.ctx.env.now
        while self.is_running() and self.valid_step():
            s = self.do_step()
        self.fire("visible_step", self, s)

    def do_step(self):
        try:
            step = next(self.generator)
            self.fire("step", self, step)
            return step
        except StopIteration:
            None

    def valid_step(self):
        now = self.ctx.env.now
        if now > self.last_sim_time:
            return False
        return True

    def start(self):
        self._create_procesess()
        self.running = True
        self._prepare()
        self.fire("start", self)

