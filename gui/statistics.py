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

class SimulationStatistics(Statistics):
    def __init__(self, simulation_tab):
        Statistics.__init__(self)
        self.sim_tab = simulation_tab
        self.create_properties()

    def create_properties(self):
        panel = self.sim_tab.properties_panel
        self.add_property("name", "Name:", "", panel)
        self.add_property("size", "Size:", "", panel)
        self.add_property("discovered_by", "Discovered by process:", "", panel)

        panel = self.sim_tab.statistics_panel
        self.add_property("sim_time", "Simulation time:", "", panel)
        self.add_property("pr_count", "Process count:", "", panel)
        self.add_property("alg", "Algorithm:", "", panel)
        self.add_property("step", "Sim steps:", "", panel)
        self.add_property("nodes_count", "Nodes:", "", panel)

    def update_node_properties(self, node):
        self.update_property("name", node.get_name())
        self.update_property("size", node.get_size())
        self.update_property("discovered_by", node.get_discoverer())

    def update_statistics(self):
        self.update_property("pr_count", len(self.sim_tab.simulator.processes))
        self.update_property("alg", self.sim_tab.simulator.processes[0].get_name())
        self.update_property("nodes_count", len(self.sim_tab.graph.nodes))
