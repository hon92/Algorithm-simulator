import paths
import sys
from gui.graphgenerator import GraphGenerator
sys.path.append(paths.ROOT)
import gtk
import window
import tab
import gobject
import appargs
import settings
from gui.dialogs import dialog
from project import Project
from sim import processfactory as pf
from gui import gladeloader as gl

settings.init()
gobject.threads_init()
pf.load()

class App():
    def __init__(self, args):
        self.project = None
        self.window = window.Window(self)
        self.window.create_tab(tab.WelcomeTab(self.window, "Welcome tab"))
        self.app_args = appargs.AppArgs(self, args)
        self.app_args.solve()

    def run(self):
        self.window.show()
        gtk.threads_enter()
        gtk.main()
        gtk.threads_leave()

    def close(self):
        if self.project:
            self.close_project()
        gtk.main_quit()

    def _open_project(self, project):
        def on_project_error(msg):
            self.window.console.writeln(msg, "err")

        project.connect("error", on_project_error)
        project.open()
        self.project = project
        project_tab = tab.ProjectTab(self.window, project)
        self.window.create_tab(project_tab)
        project_tab.load()

    def create_project(self):
        input_dialog = dialog.InputDialog("Insert project name", self.window)
        project_name = input_dialog.run()
        if project_name:
            project_file = dialog.Dialog.get_factory("xml").save_as("Save project file",
                                                                    text = project_name + ".xml")
            if project_file:
                if self.project:
                    self.project.close()
                project = Project.create_empty_project(project_file)
                project.set_name(project_name)
                project.save()
                self._open_project(project)
                msg = "Project '{0}' was created at location '{1}'"
                self.window.console.writeln(msg.format(project.get_name(),
                                                           project.get_file()))

    def open_project(self, project_file = None):
        if not project_file:
            project_file = dialog.Dialog.get_factory("xml").open("Open project")

        if project_file:
            if self.project:
                self.close_project()

            try:
                project = Project(project_file)
                msg = "Opening project at location '{0}'".format(project_file)
                self.window.console.writeln(msg)
                self._open_project(project)
                msg = "Project '{0}' was opened".format(project.get_name())
                self.window.console.writeln(msg)
            except Exception as ex:
                self.window.console.writeln(ex.message, "err")

    def close_project(self):
        if self.project:
            name = self.project.get_name()
            self.project.close()
            self.window.set_title("")
            self.project = None
            msg = "Project '{0}' was closed".format(name)
            self.window.console.writeln(msg)

    def save_project(self):
        if self.project:
            saved = self.project.save()
            if saved:
                msg = "Project '{0}' was saved".format(self.project.get_name())
                self.window.console.writeln(msg)
            else:
                msg = "Project '{0}' was not saved due to error"
                self.window.console.writeln(msg.format(self.project.get_name()), "err")

    def open_settings(self):
        settings_tab = self.window.get_tab("Settings")
        if settings_tab:
            self.window.switch_to_tab(settings_tab)
        else:
            settings_tab = tab.SettingsTab(self.window)
            self.window.create_tab(settings_tab)

    def start_simulation(self):
        if self.project:
            self.project.get_tab().run_simulations()

    def start_graphics_simulation(self):
        if self.project:
            self.project.get_tab().run_vizual_simulations()

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
                        self.project.load_graph_file(graph_file)
                        project_tab = self.window.get_tab("Project")
                        project_tab.add_graph(graph_file)
                except Exception as ex:
                    self.window.console.writeln(ex.message, "err")

            gen_dialog.destroy()
