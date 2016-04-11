import gtk

class Statistics():
    def __init__(self):
        self.properties = {}

    def add_property(self, key, label, value, panel):
        display_label = gtk.Label(label)
        value_label = gtk.Label(str(value))
        hbox = gtk.HBox()
        hbox.pack_start(display_label, False, False)
        hbox.pack_start(value_label, False, False)
        panel.pack_start(hbox, False, False)
        self.properties[key] = (display_label, value_label)

    def update_property(self, key, new_value):
        if key in self.properties:
            self.properties[key][1].set_text(str(new_value))
    