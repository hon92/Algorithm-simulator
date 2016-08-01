import threading
import Queue

class Worker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.q = Queue.Queue()
        self.task_in_progress = None

    def solve_task(self, task):
        self.task_complete()

    def run(self):
        while True:
            task = self.q.get()
            if not task:
                self.task_in_progress = None
                break
            self.task_in_progress = task
            self.solve_task(task)

    def put(self, task):
        self.q.put_nowait(task)

    def quit(self):
        with self.q.mutex:
            self.q.queue.clear()
        self.put(None)

    def task_complete(self):
        self.q.task_done()

class SimWorker(Worker):
    def __init__(self):
        Worker.__init__(self)
        self.callbacks = []
        self.error_callbacks = []

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def add_error_callback(self, callback):
        self.error_callbacks.append(callback)

    def solve_task(self, task):
        task.connect("end_simulation", self._end)
        try:
            task.start()
        except Exception as ex:
            self._error(task, ex.message)

    def _error(self, sim, msg):
        for cb in self.error_callbacks:
            cb(sim, msg)
        self.task_complete()

    def _end(self, sim):
        for cb in self.callbacks:
            cb(sim)
        self.task_complete()

    def interrupt_current_task(self):
        if self.task_in_progress:
            self.task_in_progress.stop()
