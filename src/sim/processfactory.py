import sys
import importlib
from processes import monitor


class ProcessFactory():
    def __init__(self):
        self.available_processes = []

    def load_process_from_file(self, filename, class_name):
        module = importlib.import_module(filename)
        loaded_class = getattr(module, class_name)
        if not hasattr(loaded_class, "NAME"):
            raise Exception("Process has to have NAME attribute")
        if not hasattr(loaded_class, "DESCRIPTION"):
            raise Exception("Process has to have DESCRIPTION attribute")
        if not hasattr(loaded_class, "PARAMS"):
            raise Exception("Process has to have PARAMS attribute")
        self.available_processes.append(loaded_class)

    def get_processes_names(self):
        return [p.NAME for p in self.available_processes]

    def get_process_description(self, name):
        p = self._get_process(name)
        if not p:
            raise Exception("Invalid process name")
        return p.DESCRIPTION

    def create_process(self, id, ctx, name):
        process_class = self._get_process(name)
        if not process_class:
            raise Exception("Invalid process name")

        process = process_class(id, ctx)
        mm = ctx.monitor_manager
        mm.register_process_monitor(id, monitor.MemoryMonitor(process))
        mm.register_process_monitor(id, monitor.TimeMonitor(process))
        mm.register_process_monitor(id, monitor.ProcessMonitor(process))
        mm.register_process_monitor(id, monitor.EdgeMonitor(process))
        return process

    def _get_process(self, name):
        for p in self.available_processes:
            if p.NAME == name:
                return p
        return None

process_factory = ProcessFactory()
try:
    process_factory.load_process_from_file("sim.processes.algorithms", "Algorithm1")
    process_factory.load_process_from_file("sim.processes.algorithms", "Algorithm2")
    process_factory.load_process_from_file("sim.processes.algorithms", "Algorithm3")
    process_factory.load_process_from_file("sim.processes.algorithms", "PingPongExample")
except Exception as ex:
    print ex.message
    sys.exit(1)

