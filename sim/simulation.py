import simpy
import monitor
from processes import process
from gui import events

class ProcessFactory():
    def __init__(self, env):
        self.env = env

    def create_process(self, process_type):
        for pr in process._loaded_classes:
            if pr.__name__ == process_type:
                return pr(self.env)
        return None

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
        self.process_factory = ProcessFactory(self.env)
        self.process_id_gen = -1
        self.graph = graph
        self.processes = []
        self.process_events = []

    def _generate_process_id(self):
        self.process_id_gen += 1
        return self.process_id_gen

    def _reset_process_id(self):
        self.process_id_gen = -1

    def register_process(self, process_type):
        new_process = self.process_factory.create_process(process_type)
        if new_process:
            self.processes.append(new_process)

    def register_n_processes(self, process_type, count):
        for i in xrange(count):
            self.register_process(process_type)

    def get_available_processor_types(self):
        return process.get_process_names()

    def prepare_processes(self):
        self._reset_process_id()

        for process in self.processes:
            process.graph = self.graph
            process.processes = self.processes
            process.id = self._generate_process_id()
            process.monitor = monitor.Monitor()
            process.on_start()
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
