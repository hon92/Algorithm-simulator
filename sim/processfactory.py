from processes import monitor

_pre_process_path = "sim.processes."
# tuple (class_name, file), file must be inside processes package
available_processes = [("Alg2", "alg")]

_loaded_classes = None

def load():
    global _loaded_classes
    if not _loaded_classes:
        _loaded_classes = []
        import importlib
        for cl, f in available_processes:
            module = importlib.import_module(_pre_process_path + f)
            _loaded_classes.append(getattr(module, cl))

def get_process_names():
    global _loaded_classes
    if not _loaded_classes:
        load()
    return [cl.__name__ for cl in _loaded_classes]

class ProcessFactory():
    def __init__(self, env):
        self.env = env
        self._id = -1

    def next_id(self):
        self._id += 1
        return self._id

    def reset_id(self):
        self._id = -1

    def create_process(self, graph, process_type):
        for pr in _loaded_classes:
            if pr.__name__ == process_type:
                return pr(self.next_id(),
                          self.env,
                          graph)
        return None

class DefaultProcess(ProcessFactory):
    def __init__(self, env):
        ProcessFactory.__init__(self, env)

    def create_process(self, graph, process_type):
        process = ProcessFactory.create_process(self, graph, process_type)
        if not process:
            return None
        mon_manager = process.get_monitor_manager()
        mon_manager.register_monitor(monitor.TimeMonitor(process.clock))
        mon_manager.register_monitor(monitor.MemoryMonitor(process.storage, process.clock))
        mon_manager.register_monitor(monitor.EdgeMonitor(process))
        mon_manager.register_monitor(monitor.ProcessMonitor(process))
        return process