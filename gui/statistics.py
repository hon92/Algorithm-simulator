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

class PlotStatistics(Statistics):
    def __init__(self, sim_tab):
        Statistics.__init__(self)
        self.sim_tab = sim_tab

    def create_properties(self, widget):
        sim_time = self.sim_tab.simulator.env.now
        nodes_count = self.sim_tab.simulator.graph.get_nodes_count()
        self.add_property("sim_time", "Simulation time:", sim_time, widget)

        for p in self.sim_tab.simulator.processes:
            display = "Process {0}:".format(p.id)
            val = " Calculated:{0}".format(p.edges_calculated)
            self.add_property("p{0}".format(p.id), display, val, widget) 
        self.add_property("nodes_count", "Nodes count:", nodes_count, widget)