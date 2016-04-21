import simpy
import monitor
import gobject
from processes import myprocess, spinprocess
import events

class ProcessFactory():
    def __init__(self, env):
        self.env = env
        self.types = {"MyProcess": myprocess.MyProcess,
                      "SPINProcess": spinprocess.SPINProcess
                     }

    def create_process(self, process_type):
        if self.types.has_key(process_type):
            return self.types[process_type](self.env);
        return None

    def get_types(self):
        return self.types

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
        return [t for t in self.process_factory.get_types()]

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
        except Exception:
            self.sim_status = "Canceled"
        self.fire("end_simulation", self)

        #print "Simulation status", "OK" if sim_status is None else "BAD (reason:" + str(sim_status) + ")"
        #print "Simulation completed in time:", self.env.now

        """
        sum = 0
        for p in self.processes:
            sum += p.edges_calculated
            print p.id, "q:", len(p.queue), "m:", len(p.messages), "calc:", p.edges_calculated
        print "calc sum:", sum
        not_found_nodes = [n for n in self.graph.nodes.values() if not n.is_discovered()]
        print "graph:", "not found:", len(not_found_nodes)
        """

    def stop(self):
        if self.is_running():
            for e in self.process_events:
                e.fail(simpy.core.StopSimulation("Sim stopped"))
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

    def _run(self):
        pass

    def stop(self):
        del self.processes[:]
        self.env._now = 0
        self.fire("end_simulation", self)

    def prepare(self):
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
        found_new = False
        for n in self.graph.nodes.values():
            if n.is_discovered():
                if not n.is_visible():
                    n.set_visible(True)
                    found_new = True
        return found_new

    def _create_generator(self):
        try:
            step = 0
            while True:
                self.env.step()
                step += 1
                yield step
        except simpy.core.EmptySchedule:
            pass
        except Exception as ex:
            print "VisualSimulator generator", ex.message
