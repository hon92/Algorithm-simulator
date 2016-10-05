import gtk
import paths
import settings
from misc import timer

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
    def __init__(self, tab, toolbar):
        self.simulation = tab.simulation
        self.tab = tab
        self.toolbar = toolbar
        self.buttons = self.create_buttons()
        self.step_count = 0
        self.time = 0
        self.timer = timer.Timer(settings.get("VIZ_SIMULATION_TIMER"), self.step)
        self.state = None
        self.set_state(IdleState(self))
        self.simulation.connect("start", self.on_simulation_start)
        self.simulation.connect("stop", self.on_simulation_stop)
        self.simulation.connect("end", self.on_simulation_end)
        self.simulation.connect("interrupt", self.on_simulation_error)

    def set_state(self, state):
        self.state = state
        self.tab.statusbar.push(self.tab.status_ctx,
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
                                           callback = lambda e: self.tab.zoom(1))

        buttons["zoomout"] = create_toolbutton(*buttons_conf["zoomout"],
                                           callback = lambda e: self.tab.zoom(-1))
        return buttons

    def update_sim_stats(self):
        stats = self.tab.sim_stats
        self.step_count += 1
        now = self.simulation.ctx.env.now
        diff = now - self.time
        self.time = now
        memory_peak = 0
        mm = self.simulation.ctx.monitor_manager
        mem_monitor = mm.get_process_monitor(0, "MemoryMonitor")
        if mem_monitor:
            data = mem_monitor.collect(["memory_peak"])
            for _, size in data["memory_peak"]:
                if size > memory_peak:
                    memory_peak = size

        stats.update_prop("sim_memory", memory_peak)
        stats.update_prop("sim_time", now)
        stats.update_prop("Step", self.step_count)
        stats.update_prop("Last step time", diff)

        gs = self.simulation.ctx.graph_stats
        stats.update_prop("Undiscovered nodes", gs.get_undiscovered_nodes_count())
        stats.update_prop("Undiscovered edges", gs.get_undiscovered_edges_count())

        processes = self.simulation.ctx.processes
        for p in processes:
            attr = "p{0}".format(p.get_id()) + "{0}"

            stats.update_prop(attr.format("time"),
                              p.clock.get_time())

            stats.update_prop(attr.format("memory"),
                             p.get_used_memory())

            stats.update_prop(attr.format("wait"),
                             p.clock.get_waiting_time())

            stats.update_prop(attr.format("memory_peak"),
                              p.storage.get_memory_peak())

            nodes_discovered = gs.get_discovered_nodes_by_process(p.id)
            edges_discovered = gs.get_discovered_edges_by_process(p.id)
            edges_calculated = gs.get_calculated_edges_by_process(p.id)
            stats.update_prop(attr.format("discovered_nodes"), nodes_discovered)
            stats.update_prop(attr.format("discovered_edges"), edges_discovered)
            stats.update_prop(attr.format("calculated_edges"), edges_calculated)

    def on_simulation_start(self, simulation):
        def log(message, msg_type):
            self.tab.win.console.writeln(message, msg_type)

        processes = simulation.ctx.processes
        for process in processes:
            process.connect("log", log)

        self.tab.anim_plot.set_processes(self.simulation.ctx.processes)
        self.tab.anim_plot.clear()
        self.tab.anim_plot.start()
        self.step_count = 0
        self.tab.sim_stats.init_properties()
        self.timer.start()
        self.set_state(RunningState(self))

    def on_simulation_end(self, simulation):
        self.timer.stop()
        self.set_state(IdleState(self))

    def on_simulation_stop(self, simulation):
        self.timer.stop()
        self.set_state(IdleState(self))

    def on_simulation_error(self, error_message):
        self.timer.stop()
        msg = "Error in visual simulation: {0}".format(error_message)
        self.tab.win.console.writeln(msg, "err")
        self.set_state(IdleState(self))

    def run(self):
        self.simulation.start()

    def step(self):
        if self.simulation.is_running():
            self.simulation.do_visible_step()
            self.update_sim_stats()
            self.tab.anim_plot.update()
            self.tab.redraw()
            return True

    def stop(self):
        self.timer.stop()
        self.simulation.stop()
        while self.simulation.do_step():
            pass

    def pause(self):
        is_running = self.timer.is_running()
        if is_running:
            self.timer.stop()
        else:
            self.timer.start()

