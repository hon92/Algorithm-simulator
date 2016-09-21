import threading
import Queue
from gui.events import EventSource


class Worker(threading.Thread, EventSource):
    def __init__(self, success_callback = None, error_callback = None):
        threading.Thread.__init__(self)
        EventSource.__init__(self)
        self.register_event("task_start")
        self.register_event("task_end")
        self.daemon = True
        self.q = Queue.Queue()
        self.task_in_progress = None
        self.success_callback = success_callback
        self.error_callback  = error_callback

    def solve_task(self, task):
        self.fire("task_start", task)
        self.task_complete(task)

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

    def task_complete(self, task):
        if self.success_callback:
            self.success_callback(task)
        self.fire("task_end", task)
        self.q.task_done()

    def task_error(self, error_message):
        if self.error_callback:
            self.error_callback(error_message)
        self.fire("task_end", self.task_in_progress)
        self.q.task_done()

    def clear_tasks(self):
        with self.q.mutex:
            self.q.queue.clear()

    def interrupt(self):
        pass


class SimWorker(Worker):
    def __init__(self, success_cb, error_cb):
        Worker.__init__(self, success_cb, error_cb)

    def solve_task(self, task):
        task.connect("start", lambda s: self.fire("task_start", s))
        task.connect("end", self.task_complete)
        task.connect("stop", self.task_error)
        task.connect("interrupt", self.task_error)
        task.start()

    def interrupt(self):
        if self.task_in_progress:
            self.task_in_progress.stop()

