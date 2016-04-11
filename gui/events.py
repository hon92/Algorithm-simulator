
class EventSource():
    def __init__(self):
        self.callbacks = {}

    def register_event(self, event_name):
        self.callbacks[event_name] = []

    def connect(self, event_name, callback):
        if self.callbacks.has_key(event_name):
            self.callbacks[event_name].append(callback)

    def fire(self, event_name, *args):
        if self.callbacks.has_key(event_name):
            for cb in self.callbacks[event_name]:
                cb(*(args))