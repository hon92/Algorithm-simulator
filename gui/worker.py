import threading
import Queue

class Worker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.q = Queue.Queue()

    def solve_task(self, task):
        self.task_complete()

    def run(self):
        while True:
            task = self.q.get()
            if not task:
                break
            self.solve_task(task)

    def put(self, task):
        self.q.put_nowait(task)

    def quit(self):
        self.put(None)

    def task_complete(self):
        self.q.task_done()

class SimWorker(Worker):
    def __init__(self):
        Worker.__init__(self)
        self.callbacks = []

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def solve_task(self, task):
        task.connect("end_simulation", self._end)
        task.start()

    def _end(self, sim):
        for cb in self.callbacks:
            cb(sim)
        self.task_complete()