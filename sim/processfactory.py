import importlib
from processes import monitor

_pre_process_path = "sim.processes."
# tuple (class_name, file), file must be inside processes package
available_processes = [("Algorithm1", "algorithms"),
                       ("Algorithm2", "algorithms"),
                       ("Algorithm3", "algorithms"),
                       ("PingPongExample", "algorithms")]
loaded = False
_loaded_classes = []
algs = {}

def load():
    global loaded

    if not loaded:
        for class_name, filename in available_processes:
            module = importlib.import_module(_pre_process_path + filename)
            loaded_class = getattr(module, class_name)
            algs[loaded_class.NAME] = loaded_class.DESCRIPTION
            _loaded_classes.append(loaded_class)
        loaded = True

def get_processes_names():
    return algs.keys()

def get_alg_description(algorithm_name):
    if algorithm_name in algs:
        return algs[algorithm_name]
    return ""

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
            if pr.NAME == process_type:
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