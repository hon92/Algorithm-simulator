import gobject

class Timer():
    def __init__(self, interval, callback, **args):
        self.interval = interval
        self.callback = callback
        self.timer = None
        self.running = False

    def _tick(self):
        val = self.callback()
        if val:
            return True
        else:
            self.running = False
            return False

    def start(self):
        self.timer = gobject.timeout_add(self.interval, self._tick)
        self.running = True

    def stop(self):
        if self.timer:
            if self.running:
                gobject.source_remove(self.timer)
        self.timer = None
        self.running = False

    def is_running(self):
        return self.running