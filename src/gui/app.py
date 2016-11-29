import paths
import sys
sys.path.insert(0, paths.SRC_PATH)
import gobject
import gtk
import window
import tab
import appargs
import gladeloader as gl
from gui.dialogs import dialog
from graphgenerator import GraphGenerator
from gui.projectloader import ProjectLoader

gobject.threads_init()


class App():
    def __init__(self, args):
        self.project = None
        self.window = window.Window(self)
        self.app_args = appargs.AppArgs(self, args)
        self.app_args.solve()
        self.window.create_tab(tab.WelcomeTab(self.window, "Welcome tab"))

    def run(self):
        self.window.show()
        gtk.threads_enter()
        gtk.main()
        gtk.threads_leave()

    def create_project(self):
        input_dialog = dialog.InputDialog("Insert project name", self.window)
        project_name = input_dialog.run()
        if project_name:
            project_file = dialog.Dialog.get_factory("xml").save_as("Save project file",
                                                                    text = project_name + ".xml")
            if project_file:
                if self.project:
                    self.project.close()

                try:
                    project = ProjectLoader.create_empty_project(project_file, project_name)
                    self._open_project(project)
                    msg = "Project '{0}' was created at location '{1}'"
                    self.window.console.writeln(msg.format(project.get_name(),
                                                           project.get_file()))
                except Exception as ex:
                    self.window.console.writeln(ex.message, "err")

    def open_project(self, project_file = None):
        if not project_file:
            project_file = dialog.Dialog.get_factory("xml").open("Open project")

        if project_file:
            if self.project:
                self.close_project()

            try:
                def on_project_error(msg):
                    self.window.console.writeln(msg, "err")

                msg = "Opening project at location '{0}'".format(project_file)
                self.window.console.writeln(msg)
                project = ProjectLoader.load_project(project_file, on_project_error)
                self._open_project(project)
                msg = "Project '{0}' was opened".format(project.get_name())
                self.window.console.writeln(msg)
            except IOError as ex:
                raise Exception("Project file error: {0}".format(ex))
            except Exception as ex:
                raise Exception("Project is corrupted ({0})".format(ex.message))
                #self.window.console.writeln("Project is corrupted ({0})".format(ex.message), "err")

    def _open_project(self, project):
        self.project = project
        self.project.saved = True
        project_tab = tab.ProjectTab(self.window, project)
        simulations_tab = tab.SimulationsTab(self.window, project)
        self.window.create_tab(project_tab)
        self.window.create_tab(simulations_tab)

    def save_project(self):
        if self.project:
            try:
                ProjectLoader.save_project(self.project)
                self.project.saved = True
                msg = "Project '{0}' was saved".format(self.project.get_name())
                self.window.console.writeln(msg)
            except Exception as ex:
                msg = "Project '{0}' was not saved due to error({1})"
                self.window.console.writeln(msg.format(self.project.get_name(),
                                                       ex.message), "err")

    def close_project(self):
        if self.project:
            if not self.project.is_saved():
                print "you should save your project before closing"
            name = self.project.get_name()
            self.project.close()
            self.window.set_title("")
            self.project = None
            msg = "Project '{0}' was closed".format(name)
            self.window.console.writeln(msg)

    def open_settings(self):
        settings_tab = self.window.get_tab("Settings")
        if settings_tab:
            self.window.switch_to_tab(settings_tab)
        else:
            settings_tab = tab.SettingsTab(self.window)
            self.window.create_tab(settings_tab)

    def start_simulation(self):
        if self.project:
            self.project.get_project_tab().on_sim_button_clicked(None)

    def start_graphics_simulation(self):
        if self.project:
            self.project.get_project_tab().on_viz_sim_button_clicked(None)

    def generate_graph(self):
        if self.project:
            builder = gl.GladeLoader("generate_graph_dialog").load()
            gen_dialog = builder.get_object("dialog")
            gen_dialog.set_title("Generate graph settings")
            gen_dialog.set_position(gtk.WIN_POS_CENTER)

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
            response = gen_dialog.run()
            if response:
                try:
                    graph_generator = GraphGenerator(filename_entry.get_text(),
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

            gen_dialog.destroy()

    def generate_scalability_graph(self):
        if not self.project:
            return

        project_tab = self.project.get_project_tab()
        process_type = project_tab.get_process_type()
        if not process_type:
            return

        files = project_tab.get_selected_files()
        if len(files) == 0:
            return

        model = project_tab.get_model()
        if not model:
            return

        try:
            arguments = project_tab.get_arguments()
        except Exception as ex:
            err_msg = "Algorithm parameter type error: {0}".format(ex.message)
            self.window.console.writeln(err_msg, "err")
            return

        scale_tab = tab.ScalabilityTab(self.window,
                                        process_type,
                                        arguments,
                                        model,
                                        self.project.graph_manager.get_graph(files[0]))

        self.window.create_tab(scale_tab)

    def close(self):
        if self.project:
            self.close_project()
        gtk.main_quit()

