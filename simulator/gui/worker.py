import threading
import Queue
from events import EventSource
from gobject import gobject, PRIORITY_HIGH

class Worker(threading.Thread, EventSource):
    def __init__(self):
        threading.Thread.__init__(self)
        EventSource.__init__(self)
        self.daemon = True
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
        self.clear_tasks()
        self.interrupt()
        self.put(None)

    def task_complete(self):
        self.q.task_done()
        self.task_in_progress = None

    def task_error(self, error_message):
        self.q.task_done()
        self.task_in_progress = None

    def clear_tasks(self):
        with self.q.mutex:
            self.q.queue.clear()

    def interrupt(self):
        self.task_in_progress = None

    def size(self):
        return self.q.qsize()


class SimWorker(Worker):
    def __init__(self, sim_start_cb, sim_end_cb, sim_error_cb):
        Worker.__init__(self)
        self.sim_start_cb = sim_start_cb
        self.sim_end_cb = sim_end_cb
        self.sim_error_cb = sim_error_cb

    def solve_task(self, task):
        def sim_end(sim):
            self.task_complete()
            self.sim_end_cb(sim)

        def sim_error(error):
            self.task_complete()
            self.sim_error_cb(error)

        task.connect("start", lambda s: gobject.idle_add(self.sim_start_cb, s, priority = PRIORITY_HIGH))
        task.connect("end", lambda s: gobject.idle_add(sim_end, s, priority = PRIORITY_HIGH))
        task.connect("stop", lambda e: gobject.idle_add(sim_error, e, priority = PRIORITY_HIGH))
        task.connect("interrupt", lambda e: gobject.idle_add(sim_error, e, priority = PRIORITY_HIGH))
        task.start()

    def interrupt(self):
        if self.task_in_progress:
            self.task_in_progress.disconnect("interrupt")
            self.task_in_progress.disconnect("end")
            self.task_in_progress.disconnect("stop")
            self.task_in_progress.stop()

