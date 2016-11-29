import gtk
import gobject
from gui import events


class ProgressBar(events.EventSource):
    REFRESH_TIME = 100
    def __init__(self):
        events.EventSource.__init__(self)
        self.progress_bar = gtk.ProgressBar()
        self.timer = None
        self.running = False
        self.last_tick = 0
        self.pulse = True
        self.register_event("tick")
        self.register_event("complete")

    def set_pulse(self, val):
        self.pulse = val

    def get_progress_bar(self):
        return self.progress_bar

    def set_progressbar_text(self, text):
        self.progress_bar.set_text(text)

    def set_value(self, fraction):
        self.progress_bar.set_fraction(fraction)

    def start(self):
        self.timer = gobject.timeout_add(self.REFRESH_TIME, self.tick)

    def tick(self):
        self.running = True
        fraction = self.progress_bar.get_fraction()
        self.fire("tick", fraction)
        if fraction >= 1.0:
            self.progress_bar.set_fraction(1.0)
            self.fire("complete")
            return False
        elif self.last_tick == fraction:
            if self.pulse:
                self.progress_bar.pulse()
        self.last_tick = fraction
        return True

    def stop(self):
        if self.timer:
            if self.running:
                gobject.source_remove(self.timer)
                self.running = False

