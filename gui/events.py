
class EventSource():
    def __init__(self):
        self.callbacks = {}

    def register_event(self, event_name):
        self.callbacks[event_name] = []

    def connect(self, event_name, callback):
        if event_name in self.callbacks:
            self.callbacks[event_name].append(callback)

    def disconnect(self, event_name):
        if event_name in self.callbacks:
            del self.callbacks[event_name]

    def fire(self, event_name, *args):
        if event_name in self.callbacks:
            for cb in self.callbacks[event_name]:
                cb(*(args))