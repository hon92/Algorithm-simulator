from gui.events import EventSource

_pre_process_path = "sim.processes."
# tuple (class_name, file), file must be inside processes package
available_processes = ( ("MyProcess", "myprocess"),
                        ("SPINProcess", "spinprocess"),
                        ("BFSProcess", "bfsprocess")
                      )

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


class Process(EventSource):
    def __init__(self, env):
        EventSource.__init__(self)
        self.register_event("log")
        self.env = env
        self.block_event = env.event()
        self.edges_calculated = 0
        self.step = 0

    def on_start(self):
        pass

    def run(self):
        yield

    def send_monitor_data(self, monitor_type, xval, yval):
        self.monitor.push(monitor_type, xval, yval)

    def get_time(self):
        return self.env.now

    def get_step(self):
        return self.step

    def add_step(self):
        self.step += 1

    def block_until(self):
        return self.block_event

    def unblock(self):
        if not self.block_event.triggered:
            self.block_event.succeed()

    def reset_block(self):
        self.block_event = self.env.event()

    def calculate_edge(self, val):
        self.edges_calculated += val

    def get_name(self):
        return ""

    def get_calculated_time(self):
        return self.edges_calculated

    def log(self, msg, tag = "out"):
        self.fire("log", msg, tag)
