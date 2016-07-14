import simpy
import processfactory as pf
from processes import process
from gui import events

class AbstractSimulation(events.EventSource):
    def __init__(self):
        events.EventSource.__init__(self)
        self.register_event("start_simulation")
        self.register_event("end_simulation")
        self.running = False
        self.connect("start_simulation", lambda s: self._set_running(True))
        self.connect("end_simulation", lambda s: self._set_running(False))

    def _set_running(self, val):
        self.running = val

    def start(self):
        self.prepare()
        self._run()

    def _run(self):
        pass

    def stop(self):
        pass

    def prepare(self):
        pass

    def is_running(self):
        return self.running

class Simulation(AbstractSimulation):
    def __init__(self, graph):
        AbstractSimulation.__init__(self)
        self.env = simpy.Environment()
        self.process_factory = pf.DefaultProcess(self.env)
        self.graph = graph
        self.processes = []
        self.process_events = []

    def register_process(self, process_type):
        new_process = self.process_factory.create_process(self.graph,
                                                          process_type)
        if new_process:
            self.processes.append(new_process)

    def register_n_processes(self, process_type, count):
        for i in xrange(count):
            self.register_process(process_type)

    def get_available_processor_types(self):
        return pf.get_process_names()

    def prepare_processes(self):
        self.process_factory.reset_id()

        for process in self.processes:
            op = [p for p in self.processes if p.get_id() != process.get_id()]
            process.set_processes(op)
            process.initialize()
            e = self.env.process(process.run())
            self.process_events.append(e)

    def _run(self):
        self.fire("start_simulation", self)
        try:
            self.sim_status = self.env.run()
        except simpy.core.StopSimulation:
            self.sim_status = "Canceled"
        self.fire("end_simulation", self)

    def stop(self):
        if self.is_running():
            for e in self.process_events:
                try:
                    e.fail(simpy.core.StopSimulation("Sim stopped"))
                except Exception:
                    pass
        del self.processes[:]
        self.env._now = 0

    def prepare(self):
        self.graph.reset()
        self.prepare_processes()

class VisualSimulation(Simulation):
    def __init__(self, visible_graph):
        Simulation.__init__(self, visible_graph)
        self.register_event("step")
        self.register_event("visible_step")
        self.generator = None
        self.visible_count = 0

    def _run(self):
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
