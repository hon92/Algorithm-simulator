import gtk
import paths
import settings
import tab
from canvas import Canvas
from misc import utils
from nodeselector import NodeSelector
from sim.simulation import VisualSimulation
from dialogs.simulationdialog import SimulationDialog
from plot import VizualSimPlotAnim, set_ax_color
from misc import timer, colors as color_palette
from gui import statistics

buttons_conf = {"run": ("Run new", "Run simulation", "Play-24.png"),
                "step": ("Step", "Run one step in simulation", "Left Footprint-24.png"),
                "stop": ("Stop", "Stop simulation", "Stop-24.png"),
                "zoomin": ("Zoom in", "Zoom in", "Zoom In-24.png"),
                "zoomout": ("Zoom out", "Zoom out", "Zoom Out-24.png"),
                "pause": ("Pause", "Pause simulation", "Pause-24.png"),
                "continue": ("Continue", "Continue in simulation", "Play-24.png")
                }

def switch_button(b, label, tooltip, icon_name):
    img, l = b.child.get_children()
    img.set_from_file(paths.ICONS_PATH + icon_name)
    l.set_text(label)
    b.set_tooltip_text(tooltip)

class SimulationState():
    def __init__(self, controller):
        self.controller = controller

    def run(self):
        pass

    def stop(self):
        pass

    def step(self):
        pass

class RunningState(SimulationState):
    def __init__(self, controller):
        SimulationState.__init__(self, controller)
        self.controller.buttons["step"].set_sensitive(True)
        self.controller.buttons["stop"].set_sensitive(True)
        switch_button(self.controller.buttons["run"],
                      *buttons_conf["pause"])

    def run(self):
        self.controller.pause()
        self.controller.set_state(PausedState(self.controller))

    def stop(self):
        self.controller.stop()
        self.controller.set_state(IdleState(self.controller))

    def step(self):
        if not self.controller.step():
            self.controller.set_state(IdleState(self.controller))

    def get_state_name(self):
        return "Running"

class PausedState(SimulationState):
    def __init__(self, controller):
        SimulationState.__init__(self, controller)
        switch_button(self.controller.buttons["run"],
                      *buttons_conf["continue"])

    def run(self):
        self.controller.pause()
        self.controller.set_state(RunningState(self.controller))

    def stop(self):
        self.controller.stop()
        self.controller.set_state(IdleState(self.controller))

    def step(self):
        if not self.controller.step():
            self.controller.set_state(IdleState(self.controller))

    def get_state_name(self):
        return "Paused"

class IdleState(SimulationState):
    def __init__(self, controller):
        SimulationState.__init__(self, controller)
        self.controller.buttons["stop"].set_sensitive(False)
        self.controller.buttons["step"].set_sensitive(False)
        switch_button(self.controller.buttons["run"],
                      *buttons_conf["run"])

    def run(self):
        if self.controller.run():
            self.controller.set_state(RunningState(self.controller))

    def get_state_name(self):
        return "Idle"

class SimulationController():
    def __init__(self, sim_tab, toolbar):
        self.simulator = sim_tab.simulator
        self.sim_tab = sim_tab
        self.toolbar = toolbar
        self.buttons = self.create_buttons()
        self.step_count = 0
        self.time = 0
        self.timer = timer.Timer(settings.VIZ_SIMULATION_TIMER, self.step)
        self.state = None
        self.set_state(IdleState(self))

    def set_state(self, state):
        self.state = state
        self.sim_tab.statusbar.push(self.sim_tab.status_ctx,
                                    "State: " + state.get_state_name())

    def create_buttons(self):
        buttons = {}

        def create_toolbutton(label, tooltip, icon_name, callback):
            image = gtk.Image()
            image.set_from_file(paths.ICONS_PATH + icon_name)
            image.show()
            button = self.toolbar.append_item(label,
                                    tooltip,
                                    "Private",
                                    image,
                                    callback)
            return button

        buttons["run"] = create_toolbutton(*buttons_conf["run"],
                                           callback = lambda e: self.state.run())

        buttons["step"] = create_toolbutton(*buttons_conf["step"],
                                           callback = lambda e: self.state.step())

        buttons["stop"] = create_toolbutton(*buttons_conf["stop"],
                                           callback = lambda e: self.state.stop())

        self.toolbar.append_space()

        buttons["zoomin"] = create_toolbutton(*buttons_conf["zoomin"],
                                           callback = lambda e: self.sim_tab.zoom(1))

        buttons["zoomout"] = create_toolbutton(*buttons_conf["zoomout"],
                                           callback = lambda e: self.sim_tab.zoom(-1))
        return buttons

    def update_timers(self):
        self.step_count += 1
        diff = self.simulator.env.now - self.time
        self.time = self.simulator.env.now
        self.sim_tab.sim_stats.update_prop("sim_time", self.simulator.env.now)
        self.sim_tab.sim_stats.update_prop("Step", self.step_count)
        self.sim_tab.sim_stats.update_prop("Last step time", diff)
        self.sim_tab.sim_stats.update_undiscovered(self.simulator.graph)
        self.sim_tab.sim_stats.update_processes(self.simulator.processes)
        self.sim_tab.anim_plot.update()

    def request_sim_dialog(self):
        sim_dialog = SimulationDialog(self.sim_tab.win,
                                      self.simulator.get_available_processor_types())
        result = sim_dialog.run()
        if result != gtk.RESPONSE_OK:
            sim_dialog.destroy()
            return False
        process_count = sim_dialog.get_process_count()
        process_type = sim_dialog.get_process_type()
        sim_dialog.destroy()
        self.simulator.stop()
        self.simulator.register_n_processes(process_type, process_count)
        for process in self.simulator.processes:
            process.connect("log", self._log_message)
        return True

    def set_graph_colors(self):
        cc = color_palette.new_color_cycler()
        colors = []
        for _ in xrange(len(self.simulator.processes)):
            colors.append(utils.hex_to_rgb(next(cc)))
        self.sim_tab.graph.set_colors(colors)

    def _log_message(self, msg, tag):
        self.sim_tab.win.console.writeln(msg, tag)

    def run(self):
        if not self.simulator.is_running():
            if not self.request_sim_dialog():
                return False
            self.step_count = 0
            self.set_graph_colors()
            self.simulator.start()
            self.sim_tab.sim_stats.new_simulation(self.simulator)
            self.sim_tab.clear_plots()
            self.sim_tab.anim_plot.set_processes(self.simulator.processes)
            self.sim_tab.anim_plot.start()
            self.update_timers()
            self.timer.start()
            return True
        return False

    def step(self):
        if self.simulator.is_running():
            self._step()
            self.sim_tab.redraw()
            self.update_timers()
            return True
        else:
            self.set_state(IdleState(self))
            return False

    def _step(self):
        val = self.simulator.visible_step()
        if not val:
            self.simulator.running = False

    def stop(self):
        self.timer.stop()
        self.simulator.stop()

    def pause(self):
        if self.timer.is_running():
            self.timer.stop()
        else:
            if self.simulator.is_running():
                self.timer = timer.Timer(settings.VIZ_SIMULATION_TIMER, self.step)
                self.timer.start()

    def restart(self):
        self.stop()
        self.simulator.graph.reset()
        self.sim_tab.clear_plots()
        self.sim_tab.redraw()

class VizualSimulationTab(tab.CloseTab):
    def __init__(self, window, title, project, filename):
        tab.CloseTab.__init__(self, window, title)
        self.project = project
        self.filename = filename
        self.selected_node = None
        self.graph = self.project.graph_manager.get_visible_graph(filename)
        self.graph.reset()

        builder = gtk.Builder()
        builder.add_from_file(paths.GLADE_DIALOG_DIRECTORY + "visual_sim_tab.glade")
        vbox = builder.get_object("vbox")
        toolbar = builder.get_object("toolbar")
        self.statusbar = builder.get_object("statusbar")
        self.status_ctx = self.statusbar.get_context_id("Simulation state")

        canvas = Canvas()
        canvas.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        canvas.connect("configure_event", lambda w, e: self.redraw())
        canvas.connect("button_press_event", lambda w, e: self.on_mouse_click(e))
        canvas.set_size_request(self.graph.width, self.graph.height)
        canvas_container = builder.get_object("canvascontainer")
        canvas_container.pack_start(canvas)
        self.canvas = canvas

        self.anim_plot = VizualSimPlotAnim()

        marker_button = builder.get_object("markerbutton")
        navbar_button = builder.get_object("navbarbutton")
        time_button = builder.get_object("timebutton")
        step_button = builder.get_object("stepbutton")

        marker_button.set_active(self.anim_plot.has_marker())
        navbar_button.set_active(self.anim_plot.has_navbar())
        if self.anim_plot.get_unit() == "time":
            time_button.set_active(True)
        else:
            step_button.set_active(True)

        marker_button.connect("toggled", self.on_marker_button_toggle)
        navbar_button.connect("toggled", self.on_navbar_button_toggle)
        time_button.connect("toggled", self.on_unit_change, "time")
        step_button.connect("toggled", self.on_unit_change, "step")

        plotvbox = builder.get_object("plotvbox")
        plotvbox.pack_start(self.anim_plot.create_widget(window))
        self.pack_start(vbox)
        self.simulator = VisualSimulation(self.graph)
        self.node_selector = NodeSelector(self.graph)
        self.controller = SimulationController(self, toolbar)

        properties_store = builder.get_object("propertystore")
        self.state_stats = statistics.StateStatistics(properties_store)
        self.state_stats.init()

        info_store = builder.get_object("infostore")
        self.sim_stats = statistics.SimulationStatistics(info_store)
        self.sim_stats.init()
        self.sim_stats.update_graph(self.filename, self.graph)
        self.show_all()


#     def _create_right_panel(self):
#         self.anim_plot = VizualSimPlotAnim(self.init_plots,
#                                            self.animate,
#                                            self.frames_gen)
#         sw = gtk.ScrolledWindow()
#         sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
#         sw.add_with_viewport(self.anim_plot.get_widget())
# 
#         def on_configure(w,e):
#             width = w.allocation.width
#             height = w.allocation.height
#             if width == e.width and height == e.height:
#                 return
#             sw.set_size_request(int(e.width * 0.3), int(e.height * 0.3))
#             self.hpaned.set_position(e.width - sw.allocation.width)
# 
#         self.win.connect("configure_event", on_configure)
#         sw.set_size_request(int(self.win.allocation.width * 0.3),
#                             int(self.win.allocation.height * 0.3))
#         self.hpaned.set_position(self.win.allocation.width - sw.allocation.width)
#         return sw

    def on_marker_button_toggle(self, button):
        marker = ""
        if button.get_active():
            marker = "o"

        self.anim_plot.set_marker(marker)

    def on_navbar_button_toggle(self, button):
        self.anim_plot.show_navbar(button.get_active())

    def on_unit_change(self, button, data):
        if button.get_active():
            self.anim_plot.set_unit(data)

    def redraw(self):
        self.canvas.set_color(240,240,240)
        self.canvas.draw_rectangle(0, 0, self.canvas.allocation.width,
                                   self.canvas.allocation.height, True)
        self.graph.draw(self.canvas)
        self.canvas.repaint()

    def zoom(self, direction = 1, step = 0.2):
        current_zoom = self.canvas.get_zoom()
        if direction == 1:
            if current_zoom + step <= 1:
                current_zoom += step
        else:
            if round(current_zoom, 1) - step > 0.0:
                current_zoom -= step

        self.canvas.set_zoom(current_zoom)
        self.redraw()

    def switch_selected_node(self, node):
        if self.selected_node:
            self.selected_node.is_selected = False

        if node:
            self.selected_node = node
            self.selected_node.is_selected = True
            self.update_node_info(node)
        else:
            self.state_stats.reset()
        self.redraw()

    def on_mouse_click(self, e):
        if e.button != 1:
            return
        selected_node = self.node_selector.get_node_at(int(e.x), int(e.y))
        self.switch_selected_node(selected_node)

    def update_node_info(self, node):
        self.state_stats.update(node, self.simulator)

    def clear_plots(self):
        for ax in self.anim_plot.get_figure().axes:
            for line in ax.get_lines():
                line.remove()
        self.anim_plot.get_figure().canvas.draw()

    def close(self):
        self.controller.stop()
        self.anim_plot.dispose()
        self.project.graph_manager.return_graph(self.filename,
                                                self.graph, True)
        self.canvas.dispose()
        tab.CloseTab.close(self)
