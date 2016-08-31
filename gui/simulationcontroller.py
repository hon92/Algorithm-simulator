import gtk
import paths
import settings
from misc import utils
from dialogs.simulationdialog import SimulationDialog
from misc import timer, colors as color_palette


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
        self.timer = timer.Timer(settings.get("VIZ_SIMULATION_TIMER"), self.step)
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
            return None
        process_count = sim_dialog.get_process_count()
        process_type = sim_dialog.get_process_type()
        sim_dialog.destroy()
        return process_count, process_type

    def set_graph_colors(self):
        cc = color_palette.new_color_cycler()
        colors = []
        for _ in xrange(len(self.simulator.processes)):
            colors.append(utils.hex_to_rgb(next(cc)))
        self.sim_tab.graph.set_colors(colors)

    def _log_message(self, msg, tag):
        self.sim_tab.win.console.writeln(msg, tag)

    def prepare_new_run(self, process_count, process_type):
        self.simulator.stop()
        self.simulator.register_n_processes(process_type, process_count)
        for process in self.simulator.processes:
            process.connect("log", self._log_message)

    def run(self, sim_properties = None):
        if not self.simulator.is_running():
            if not sim_properties:
                result = self.request_sim_dialog()
                if result:
                    self.prepare_new_run(result[0], result[1])
                else:
                    return False
            else:
                self.prepare_new_run(sim_properties["process_count"],
                                     sim_properties["process_type"])
            self.step_count = 0
            self.set_graph_colors()
            self.simulator.start()
            self.sim_tab.sim_stats.new_simulation(self.simulator)
            self.sim_tab.clear_plots()
            self.sim_tab.anim_plot.set_processes(self.simulator.processes)
            self.sim_tab.anim_plot.start()
            self.update_timers()
            self.timer.start()
            self.set_state(RunningState(self))
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

