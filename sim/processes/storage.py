from gui.events import EventSource
from collections import deque

class Storage(EventSource):
    def __init__(self):
        EventSource.__init__(self)
        self.register_event("push")
        self.register_event("pop")
        self.current = 0
        self.max = self.current
        self.container = None

    def get_size(self):
        return self.current

    def get_max(self):
        return self.max

    def get(self):
        self.fire("pop")
        self.current -= 1
        return self.get_item()

    def put(self, val):
        self.current += 1
        if self.current > self.max:
            self.max = self.current
        self.fire("push")
        self.put_item(val)

    def get_item(self):
        pass

    def put_item(self, val):
        pass

class StackStorage(Storage):
    def __init__(self):
        Storage.__init__(self)
        self.container = []

    def put_item(self, val):
        self.container.append(val)

    def get_item(self):
        return self.container.pop()

class QueueStorage(Storage):
    def __init__(self):
        Storage.__init__(self)
        self.container = deque()

    def put_item(self, val):
        self.container.append(val)

    def get_item(self):
        return self.container.popleft()

