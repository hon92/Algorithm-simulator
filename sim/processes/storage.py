from gui.events import EventSource
from collections import deque

class Storage(EventSource):
    def __init__(self):
        EventSource.__init__(self)
        self.register_event("push")
        self.register_event("pop")
        self.register_event("size_exceeded")
        self.current = 0
        self.max_size = self.current
        self.container = None

    def get_size(self):
        return self.current

    def get_max_size(self):
        return self.max_size

    def get(self):
        item = self.get_item()
        self.fire("pop", item)
        self.current -= 1
        return item

    def put(self, val):
        self.current += 1
        if self.current > self.max_size:
            self.fire("size_exceeded", self.current, self.max_size)
            self.max_size = self.current
        self.fire("push", val)
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

