
class Property():
    def __init__(self, name, value, tooltip, key = None):
        self.name = name
        self.value = value
        self.tooltip = tooltip
        self.key = name
        if key:
            self.key = key

class ChildProperty(Property):
    def __init__(self, parent, name, value, tooltip, key = None):
        Property.__init__(self, name, value, tooltip, key)
        self.parent = parent

class Statistics():
    def add_prop(self, property):
        pass

    def init(self):
        pass

    def reset(self):
        pass

    def update_prop(self, prop_key, new_val):
        pass

class TreeViewStatistics(Statistics):
    def __init__(self, store):
        self.s = store
        self.props = {} # key -> property key, value -> path

    def add_prop(self, property):
        i = self.s.append(property.parent, [property.name,
                                             property.value,
                                             property.tooltip])
        path = self.s.get_path(i)
        self.props[property.key] = (path, property)
        return i

    def update_prop(self, prop_key, new_val):
        path, _ = self.props[prop_key]
        self.s[path][1] = str(new_val)

    def get_prop(self, prop_key):
        path, _ = self.props[prop_key]
        return self.s[path][1]

    def reset(self):
        for p in self.props.keys():
            _, prop = self.props[p]
            self.update_prop(p, prop.value)

class StateStatistics(TreeViewStatistics):
    def __init__(self, properties_store):
        TreeViewStatistics.__init__(self, properties_store)

    def init(self):
        i = self.add_prop(ChildProperty(None, "Info", "", ""))
        self.add_prop(ChildProperty(i,
                                    "Name",
                                    "init",
                                    "State unique name"))
        self.add_prop(ChildProperty(i,
                                    "Size",
                                    "-1",
                                    "Size of selected state in state space"))
        self.add_prop(ChildProperty(i,
                                    "Visible",
                                    "False",
                                    ""))
        self.add_prop(ChildProperty(i,
                                    "Succesors",
                                    "-1",
                                    "Count of edges from state"))
        self.add_prop(ChildProperty(i,
                                    "Discoverd by",
                                    "-1",
                                    ""))
        self.add_prop(ChildProperty(i,
                                    "Undiscovered succesors",
                                    "-1",
                                    ("Count of undiscovered nodes, which this state can "
                                    "immediate reach and they are not discovered yet")))
        self.add_prop(ChildProperty(i,
                                    "Unfinished succesors",
                                    "-1",
                                    ("Count of unfinished nodes, which this state can "
                                    "immediate reach and they are not finished yet")))

        """
        i = self.add_prop(ChildProperty(None, "Simulation", "", ""))
        self.add_prop(ChildProperty(i,
                                    "Discovered by",
                                    "-1",
                                    ""))
        self.add_prop(ChildProperty(i,
                                    "Completed by",
                                    "-1",
                                    ""))
        i = self.add_prop(ChildProperty(None, "Time", "", ""))
        self.add_prop(ChildProperty(i,
                                    "Discovered time",
                                    "-1",
                                    ""))
        self.add_prop(ChildProperty(i,
                                    "Completed time",
                                    "-1",
                                    ""))
        self.add_prop(ChildProperty(i,
                                    "Waiting for completing",
                                    "-1",
                                    ""))

        i = self.add_prop(ChildProperty(None, "Steps", "", ""))
        self.add_prop(ChildProperty(i,
                                    "Discovered in step",
                                    "-1",
                                    ""))
        self.add_prop(ChildProperty(i,
                                    "Completed in step",
                                    "-1",
                                    ""))
        """

    def update(self, state, simulator):
        self.update_prop("Name", state.get_name())
        self.update_prop("Size", state.get_size())
        node = simulator.graph.get_node(state.get_name())
        edges = node.get_edges()
        self.update_prop("Succesors", len(edges))
        self.update_prop("Undiscovered succesors",
                         len([e for e in edges if e.get_discoverer() == -1]))
        self.update_prop("Unfinished succesors",
                         len([e for e in edges if e.get_complete() == -1]))
        self.update_prop("Visible", node.get_discoverer() != -1)
        self.update_prop("Discoverd by", node.get_discoverer())

class SimulationStatistics(TreeViewStatistics):
    def __init__(self, info_store):
        TreeViewStatistics.__init__(self, info_store)
        self.process_path = None

    def init(self):
        i = self.add_prop(ChildProperty(None, "Simulation", "", ""))
        self.add_prop(ChildProperty(i,
                                    "Time",
                                    "-1",
                                    "",
                                    "sim_time"))
        self.add_prop(ChildProperty(i,
                                    "Step",
                                    "-1",
                                    ""))
        self.add_prop(ChildProperty(i,
                                    "Last step time",
                                    "-1",
                                    ""))
        self.add_prop(ChildProperty(i,
                                    "Algorithm",
                                    "N/A",
                                    ""))
        self.add_prop(ChildProperty(i,
                                    "Process count",
                                    "-1",
                                    ""))

        i = self.add_prop(ChildProperty(None, "Graph", "", ""))
        self.add_prop(ChildProperty(i,
                                    "Name",
                                    "",
                                    ""))
        self.add_prop(ChildProperty(i,
                                    "Nodes count",
                                    "-1",
                                    ""))
        self.add_prop(ChildProperty(i,
                                    "Edges count",
                                    "-1",
                                    ""))
        self.add_prop(ChildProperty(i,
                                    "Undiscovered nodes",
                                    "-1",
                                    ""))
        self.add_prop(ChildProperty(i,
                                    "Undiscovered edges",
                                    "-1",
                                    ""))

    def init_processes(self, count):
        pi = self.add_prop(ChildProperty(None, "Processes", "", ""))
        self.process_path = self.s.get_path(pi)

        for p in range(count):
            key = "p{0}".format(p)
            attr = key + "{0}"
            i = self.add_prop(ChildProperty(pi, "Process", str(p), ""))

            self.add_prop(ChildProperty(i,
                                        "Id",
                                        p,
                                        ""))
            self.add_prop(ChildProperty(i,
                                        "Time",
                                        "0",
                                        "",
                                        attr.format("time")))
            self.add_prop(ChildProperty(i,
                                        "Waiting time",
                                        "0",
                                        "",
                                        attr.format("wait")))
            self.add_prop(ChildProperty(i,
                                        "Storage size",
                                        "0",
                                        "",
                                        attr.format("storage")))
            self.add_prop(ChildProperty(i,
                                        "Discovered states count",
                                        "0",
                                        "",
                                        attr.format("disc_states_count")))
            self.add_prop(ChildProperty(i,
                                        "Calculated states count",
                                        "0",
                                        "",
                                        attr.format("calc_states_count")))

    def set_process_count(self, process_count):
        if self.process_path:
            i = self.s.get_iter(self.process_path)
            self.s.remove(i)
        self.init_processes(process_count)

    def new_simulation(self, simulator):
        processes = simulator.processes
        self.set_process_count(len(processes))
        self.update_prop("Algorithm", processes[0].get_name())
        self.update_prop("Process count", len(processes))

    def update_graph(self, filename, graph):
        self.update_prop("Name", filename)
        self.update_prop("Nodes count", graph.get_nodes_count())
        self.update_prop("Edges count", graph.get_edges_count())
        self.update_undiscovered(graph)

    def update_undiscovered(self, graph):
        undiscovered_nodes = graph.get_nodes_count()
        undiscovered_edges = graph.get_edges_count()

        for _, node in graph.nodes.iteritems():
            if node.is_discovered():
                undiscovered_nodes -= 1
            for edge in node.get_edges():
                if edge.is_discovered():
                    undiscovered_edges -= 1
        self.update_prop("Undiscovered nodes", undiscovered_nodes)
        self.update_prop("Undiscovered edges", undiscovered_edges)

    def update_processes(self, processes):
        for p in processes:
            attr = "p{0}".format(p.get_id()) + "{0}"

            self.update_prop(attr.format("time"),
                             p.clock.get_time())

            self.update_prop(attr.format("storage"),
                             p.storage.get_size())

            wt = float(self.get_prop(attr.format("wait")))
            if (p.env.now - p.clock.get_time()) > wt:
                wt = p.env.now - p.clock.get_time()

            self.update_prop(attr.format("wait"),
                             wt)

            mm = p.get_monitor_manager()
            edge_mon = mm.get_monitor("EdgeMonitor")
            data = edge_mon.collect()
            disc_data = data["edge_discovered"]
            calc_data = data["edge_calculated"]
            self.update_prop(attr.format("disc_states_count"),
                             len(disc_data))

            self.update_prop(attr.format("calc_states_count"),
                             len(calc_data))

