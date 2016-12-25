

class Property():
    def __init__(self, parent, id, value, tooltip, key = None):
        self.parent = parent
        self.id = id
        self.value = value
        self.tooltip = tooltip
        self.key = id
        if key:
            self.key = key


class Statistics():
    def __init__(self, liststore):
        self.ls = liststore
        self.props = {} # key -> property key, value -> path

    def add_prop(self, property):
        i = self.ls.append(property.parent, [property.id + ": ",
                                             property.value,
                                             property.tooltip])
        path = self.ls.get_path(i)
        self.props[property.key] = (path, property)
        return i

    def update_prop(self, prop_key, new_val):
        path, _ = self.props[prop_key]
        self.ls[path][1] = str(new_val)

    def get_prop(self, prop_key):
        path, _ = self.props[prop_key]
        return self.ls[path][1]

    def reset(self):
        for p in self.props.keys():
            _, prop = self.props[p]
            self.update_prop(p, prop.value)


class StateStatistics(Statistics):
    def __init__(self, properties_store):
        Statistics.__init__(self, properties_store)
        self.init_properties()

    def init_properties(self):
        i = self.add_prop(Property(None, "Info", "", "Info section"))
        self.add_prop(Property(i,
                               "Name",
                               "",
                               "State unique id"))
        self.add_prop(Property(i,
                               "Size",
                               "",
                               "Size of selected state in state space"))
        self.add_prop(Property(i,
                               "Visible",
                               "",
                               "Visibility of node"))
        self.add_prop(Property(i,
                               "Succesors",
                               "",
                               "Count of edges from state"))
        self.add_prop(Property(i,
                               "Discoverd by",
                               "",
                               "Which process discovered this node"))
        self.add_prop(Property(i,
                               "Undiscovered succesors",
                               "",
                               ("Count of undiscovered nodes, which this state can "
                                "immediate reach and they are not discovered yet")))
        self.add_prop(Property(i,
                               "Unfinished succesors",
                               "",
                               ("Count of unfinished nodes, which this state can "
                                "immediate reach and they are not finished yet")))

    def update(self, node, simulation):
        self.update_prop("Name", node.get_id())
        self.update_prop("Size", node.get_size())
        edges = node.get_edges()
        self.update_prop("Succesors", len(edges))
        gs = simulation.ctx.graph_stats

        undiscovered_edges = [e for e in edges if not gs.is_edge_discovered(e)]
        uncomplete_edges = [e for e in edges if not gs.is_edge_calculated(e)]

        node_discoverer = gs.get_node_discoverer(node)
        if node_discoverer is None:
            node_discoverer = "N/A"

        self.update_prop("Undiscovered succesors", len(undiscovered_edges))
        self.update_prop("Unfinished succesors", len(uncomplete_edges))
        self.update_prop("Visible", gs.is_node_visible(node))
        self.update_prop("Discoverd by", node_discoverer)


class SimulationStatistics(Statistics):
    def __init__(self, info_store, simulation):
        Statistics.__init__(self, info_store)
        self.simulation = simulation

    def init_properties(self):
        self.ls.clear()
        ctx = self.simulation.ctx
        process_type = self.simulation.get_process_type()
        process_count = self.simulation.get_process_count()
        network_model = ctx.network_model.get_name()
        process_model = ctx.process_model.get_name()
        time = self.simulation.ctx.env.now
        filename = ctx.graph.filename
        gs = ctx.graph_stats
        nodes_count = gs.get_nodes_count()
        edges_count = gs.get_edges_count()
        undiscovered_nodes_count = gs.get_undiscovered_nodes_count()
        undiscovered_edges_count = gs.get_undiscovered_edges_count()
        memory_peak = 0
        mem_monitor = ctx.monitor_manager.get_monitor("GlobalMemoryMonitor")
        if mem_monitor:
            mem_usage_entry = "memory_usage"
            data = mem_monitor.collect([mem_usage_entry])
            for _, size in data[mem_usage_entry]:
                if size > memory_peak:
                    memory_peak = size

        i = self.add_prop(Property(None, "Simulation", "", "Simulation section"))
        self.add_prop(Property(i,
                               "Time",
                               time,
                               "Simulation time",
                               "sim_time"))

        self.add_prop(Property(i,
                               "Memory peak",
                               memory_peak,
                               "Maximum memory used all processes in simulation",
                               "sim_memory"))

        self.add_prop(Property(i,
                               "Step",
                               "",
                               "Step count in simulation"))
        self.add_prop(Property(i,
                               "Last step time",
                               "",
                               "Time of last step in simulation"))
        self.add_prop(Property(i,
                               "Algorithm",
                               process_type,
                               "Algorithm which was used for simulation"))
        param_prop = self.add_prop(Property(i,
                                            "Algorithm parameters",
                                            "",
                                            "Parameters available in algorithm"))

        for arg_name, arg_val in ctx.arguments.iteritems():
            self.add_prop(Property(param_prop,
                                   arg_name,
                                   str(arg_val),
                                   "'{0}' algorithm parameter".format(arg_name)))

        self.add_prop(Property(i,
                               "Network model",
                               network_model,
                               "Model which define network communication"))

        self.add_prop(Property(i,
                               "Process model",
                               process_model,
                               "Model which define process speed"))

        self.add_prop(Property(i,
                               "Process count",
                               process_count,
                               "Count of used processes"))

        i = self.add_prop(Property(None, "Graph", "", "Graph section"))
        self.add_prop(Property(i,
                               "Filename",
                               filename,
                               "Absolute path to graph file"))
        self.add_prop(Property(i,
                               "Nodes count",
                               nodes_count,
                               "Nodes (states) count in graph"))
        self.add_prop(Property(i,
                               "Edges count",
                               edges_count,
                               "Edges count in graph"))
        self.add_prop(Property(i,
                               "Undiscovered nodes",
                               undiscovered_nodes_count,
                               "The number of nodes (states) that had not been discovered"))
        self.add_prop(Property(i,
                               "Undiscovered edges",
                               undiscovered_edges_count,
                               "The number of edges that had not been discovered"))
        self.init_processes_properties()

    def init_processes_properties(self):
        processes = self.simulation.ctx.processes

        pi = self.add_prop(Property(None, "Processes", "", "Processes section"))
        gs = self.simulation.ctx.graph_stats

        for pr in processes:
            key = "p{0}".format(pr.id)
            attr = key + "{0}"

            time = pr.clock.get_time()
            memory = pr.get_used_memory()
            memory_peak = 0
            mm = pr.ctx.monitor_manager
            mem_monitor = mm.get_process_monitor(pr.id, "MemoryMonitor")
            mem_usage_entry = "memory_usage"
            data = mem_monitor.collect([mem_usage_entry])
            for sim_time, size in data[mem_usage_entry]:
                if size > memory_peak:
                    memory_peak = size

            waiting_time = self.simulation.ctx.env.now - time
            nodes_discovered = gs.get_discovered_nodes_by_process(pr)
            edges_discovered = gs.get_discovered_edges_by_process(pr)
            edges_calculated = gs.get_calculated_edges_by_process(pr)

            i = self.add_prop(Property(pi,
                                       "Process",
                                       pr.id,
                                       "Process section"))

            self.add_prop(Property(i,
                                   "Id",
                                   pr.id,
                                   "Process id"))

            self.add_prop(Property(i,
                                   "Time",
                                   time,
                                   "Time which process worked",
                                   attr.format("time")))

            self.add_prop(Property(i,
                                   "Waiting time",
                                   waiting_time,
                                   "Time which process was in waiting state",
                                   attr.format("wait")))

            self.add_prop(Property(i,
                                   "Used memory",
                                   memory,
                                   "Actual memory usage of process",
                                   attr.format("memory")))

            self.add_prop(Property(i,
                                   "Memory peak",
                                   memory_peak,
                                   "Maximum memory used by process",
                                   attr.format("memory_peak")))

            self.add_prop(Property(i,
                                   "Nodes discovered",
                                   nodes_discovered,
                                   "Count of discovered nodes (states) by process",
                                   attr.format("discovered_nodes")))

            self.add_prop(Property(i,
                                   "Edges discovered",
                                   edges_discovered,
                                   "Count of discovered edges by process",
                                   attr.format("discovered_edges")))

            self.add_prop(Property(i,
                                   "Edges calculated",
                                   edges_calculated,
                                   "Count of calculated edges by process",
                                   attr.format("calculated_edges")))

