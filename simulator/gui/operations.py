import gtk
import gladeloader as gl
import events
import graphgenerator
import tab
from dialogs import dialog
from simulator.sim import processfactory as pf


class Operation(events.EventSource):
    def __init__(self):
        events.EventSource.__init__(self)

    def perform(self):
        pass


class GenerateGraph(Operation):
    def __init__(self, app):
        Operation.__init__(self)
        self.project = app.project
        self.window = app.window

    def perform(self):
        builder = gl.GladeLoader("generate_graph_dialog").load()
        gen_dialog = builder.get_object("dialog")
        filename_entry = builder.get_object("filename_entry")
        nodes_count_spin = builder.get_object("nodes_count_spin")
        edges_count_spin = builder.get_object("edges_count_spin")
        seed_spin = builder.get_object("seed_spin")
        file_chooser_button = builder.get_object("file_chooser_button")
        insert_checkbutton = builder.get_object("insert_checkbutton")
        properties = {}

        def on_file_button_clicked(w):
            graph_file = dialog.Dialog.get_factory("xml").save_as("Save graph to file")
            if not graph_file:
                graph_file = ""
            filename_entry.set_text(graph_file)

        file_chooser_button.connect("clicked", on_file_button_clicked)
        try:
            response = gen_dialog.run()
            if response == 1:
                try:
                    graph_generator = graphgenerator.GraphGenerator(filename_entry.get_text(),
                                                     nodes_count_spin.get_value_as_int(),
                                                     edges_count_spin.get_value_as_int(),
                                                     properties,
                                                     seed_spin.get_value_as_int())
    
                    graph_file = graph_generator.create_graph()
                    self.window.console.writeln("Graph generated to file {0}".format(graph_file))
                    if insert_checkbutton.get_active():
                        self.project.add_file(graph_file)
                        project_tab = self.window.get_tab("Project")
                        project_tab.add_graph(graph_file)
                except Exception as ex:
                    self.window.console.writeln(ex.message, "err")
        finally:
            gen_dialog.destroy()


class ScalabilityDialog(Operation):
    def __init__(self, app):
        self.project = app.project
        self.window = app.window
        self.params = []

    def perform(self):
        builder = gl.GladeLoader("scalability_dialog").load()
        dialog = builder.get_object("dialog")
        graphs_combobox = builder.get_object("graphs_combobox")
        processes_combobox = builder.get_object("algorithm_combobox")
        network_models_combobox = builder.get_object("network_model_combobox")
        process_models_combobox = builder.get_object("process_model_combobox")
        parameters_vbox = builder.get_object("parameters_vbox")

        graph_files = self.project.graph_manager.get_graph_files()
        process_models = pf.process_factory.get_process_models()
        network_models = pf.process_factory.get_network_models()
        processes = pf.process_factory.get_processes_names()

        for filename in graph_files:
            graphs_combobox.append_text(filename)

        if len(graph_files) > 0:
            graphs_combobox.set_active(0)

        for process in processes:
            processes_combobox.append_text(process)

        if len(processes) > 0:
            processes_combobox.set_active(0)

        for net_model in network_models:
            network_models_combobox.append_text(net_model)

        if len(network_models) > 0:
            network_models_combobox.set_active(0)

        for pr_model in process_models:
            process_models_combobox.append_text(pr_model)

        if len(process_models) > 0:
            process_models_combobox.set_active(0)

        def show_params(parameters_vbox, params):
            parameters_vbox.foreach(lambda child: parameters_vbox.remove(child))

            if len(params) == 0:
                hb = gtk.HBox()
                hb.pack_start(gtk.Label("No parameters"))
                parameters_vbox.pack_start(hb)
                parameters_vbox.show_all()
                return

            self.params = []
            for param, (value, param_type) in params.iteritems():
                hbox = gtk.HBox()
                hbox.pack_start(gtk.Label(param))
                entry = gtk.Entry()
                entry.set_text(str(value))
                hbox.pack_start(entry, padding = 10)
                hbox.show_all()
                parameters_vbox.pack_start(hbox, False, padding = 10)
                self.params.append((param, entry, param_type))

        def on_process_change(combobox):
            process_text = combobox.get_active_text()
            if process_text:
                params = pf.process_factory.get_process_parameters(process_text)
                show_params(parameters_vbox, params)

        processes_combobox.connect("changed", on_process_change)
        on_process_change(processes_combobox)

        try:
            response = dialog.run()

            if response == 1:
                process_min = builder.get_object("process_min_spin_button").get_value()
                process_max = builder.get_object("process_max_spin_button").get_value()
                process_step = builder.get_object("process_step_spin_button").get_value()
                is_stochastic = builder.get_object("stochastic_check_button").get_active()
                stochastic_repeat = builder.get_object("stochastic_spin_button").get_value()
                graph_filename = graphs_combobox.get_active_text()
                process = processes_combobox.get_active_text()
                network_model_name = network_models_combobox.get_active_text()
                process_model_name = process_models_combobox.get_active_text()
                network_model = pf.process_factory.get_network_model(network_model_name)
                process_model = pf.process_factory.get_process_model(process_model_name)
                arguments = {}
                try:
                    for param_key, param_entry, p_type in self.params:
                        val = p_type(param_entry.get_text())
                        arguments[param_key] = val
                except Exception as ex:
                    self.window.console.writeln("Algorithm parameter error: {0}".format(ex.message), "err")
                    return

                if process_min > process_max:
                    self.window.console.writeln("Process minimum count can't be smaller then process maximum count", "err")
                    return

                if not network_model:
                    self.window.console.writeln("Network model must be specified", "err")
                    return

                if not network_model:
                    self.window.console.writeln("Process model must be specified", "err")
                    return

                if not process:
                    self.window.console.writeln("No algorithm specified", "err")
                    return

                if not graph_filename:
                    self.window.console.writeln("No graph file specified", "err")
                    return

                scale_tab = tab.ScalabilityTab(self.window,
                                               process,
                                               arguments,
                                               network_model,
                                               process_model,
                                               self.project.graph_manager.get_graph(graph_filename),
                                               int(process_min),
                                               int(process_max),
                                               int(process_step),
                                               is_stochastic,
                                               int(stochastic_repeat))
                self.window.create_tab(scale_tab)
        finally:
            dialog.destroy()

