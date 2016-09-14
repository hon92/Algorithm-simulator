import simpy
from gui import events
from sim.processes.process import ProcessContext, Process
from sim.processes.monitor import MonitorManager

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

    def is_running(self):
        return self.running

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
                    e.fail(simpy.core.StopSimulation("Simulation was interrupted"))
                except Exception:
                    pass
            self.processes_events = []
            self.ctx.processes = []
            self.ctx.env._now = 0
            self.fire("stop", self)

    def _run(self):
        self.run()
        self.running = False
        self.fire("end", self)

    def _prepare(self):
        self.processes_events = []
        for p in self.ctx.processes:
            p.init()
            e = self.ctx.env.process(p.run())
            self.processes_events.append(e)
        self.prepare()

    def run(self):
        try:
            error = self.ctx.env.run()
        except simpy.core.StopSimulation:
            if error:
                self.fire("stop")
        except Exception as ex:
            print ex.message
            self.fire("interrupt", ex.message)

    def prepare(self):
        pass

    def create_processes(self):
        processes = []
        class Pro(Process):
            def __init__(self, ctx):
                Process.__init__(self, 1, "test", ctx)
            def run(self):
                while True:
                    yield self.ctx.env.timeout(1)
                    self.communicator.send_node("dqd", 1)
                    print "test"
                    if self.ctx.env.now > 3:
                        break

        from processes import algorithms as alg
        for i in xrange(self.process_count):
            algor = Pro(self.ctx)
            processes.append(algor)
        return processes


class Simulation(AbstractSimulation):
    def __init__(self, process_type, process_count, graph, arguments = None):
        AbstractSimulation.__init__(self, process_type, process_count, arguments)
        self.ctx.graph = graph
        self.graph = graph #REMOVE THIS

    def prepare(self):
        self.ctx.graph.reset()

    def create_processes(self):
        processes = []
        class Pro(Process):
            def __init__(self, ctx):
                Process.__init__(self, 0, "test", ctx)
            def run(self):
                while True:
                    yield self.ctx.env.timeout(1)
                    self.communicator.send_node("dqd", 0)
                    print "test"
                    if self.ctx.env.now > 3:
                        break

        from processes import algorithms as alg
        for i in xrange(self.process_count):
            algor = Pro(self.ctx)
            processes.append(algor)
        return processes

        from processes import algorithms as al
        alg = al.Algorithm1(0, self.ctx)
        return [alg]

class VisualSimulation(Simulation):
    def __init__(self, visible_graph):
        Simulation.__init__(self, visible_graph)
        self.register_event("step")
        self.register_event("visible_step")
        self.generator = None
        self.visible_count = 0

    def run(self):
        pass

    def stop(self):
        del self.processes[:]
        self.env._now = 0
        self.fire("end_simulation", self)

    def prepare(self):
        self.visible_count = 0
        self.graph.reset()
        self.prepare_processes()
        self.generator = self._create_generator()
        self.fire("start_simulation", self)

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
        curr = self.graph.get_discovered_nodes_count()
        if curr != self.visible_count:
            self.visible_count = curr
            return True
        return False

    def _create_generator(self):
        try:
            step = 0
            while True:
                self.env.step()
                step += 1
                yield step
        except simpy.core.EmptySchedule:
            pass
        #except Exception as ex:
         #   print "VisualSimulator generator", ex.message
