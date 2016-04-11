import gtk
import gobject
import events
from sim import plot

class Tab(gtk.VBox):
    def __init__(self, title):
        gtk.VBox.__init__(self)
        self.show()
        self.title_text = title
        self.notebook = None

    def set_title(self, title):
        self.title_text = title

    def get_title(self):
        return self.title_text

    def get_tab_label(self):
        return gtk.Label(self.title_text)

class CloseTab(Tab):
    def __init__(self, title):
        Tab.__init__(self, title)
        self.close_button = self._prepare_close_button()
        self.close_button.connect("clicked", self.on_close, self)

    def _prepare_close_button(self):
        close_image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        btn = gtk.Button()
        btn.set_relief(gtk.RELIEF_NONE)
        btn.set_focus_on_click(False)
        btn.add(close_image)
        style = gtk.RcStyle()
        style.xthickness = 0
        style.ythickness = 0
        btn.modify_style(style)
        return btn

    def get_tab_label(self):
        hbox = gtk.HBox(False, 0)
        hbox.pack_start(gtk.Label(self.title_text))
        hbox.pack_start(self.close_button, False, False)
        hbox.show_all()
        return hbox

    def on_close(self, w, tab):
        if self.notebook:
            page_number = self.notebook.page_num(tab)
            self.notebook.remove_page(page_number)

    def close(self):
        self.on_close(self, self)

class WelcomeTab(CloseTab):
    def __init__(self, title):
        CloseTab.__init__(self, title)
        self.pack_start(gtk.Label("Welcome in simulator"))


class ProgressBarTab(CloseTab):
    REFRESH_TIME = 100
    def __init__(self, title):
        CloseTab.__init__(self, title)
        self.progress_bar = gtk.ProgressBar()
        self.timer = None
        self.running = False
        self.interrupt = False

    def set_progressbar_text(self, text):
        self.progress_bar.set_text(text)

    def start(self):
        self.timer = gobject.timeout_add(self.REFRESH_TIME, self.tick)

    def stop(self):
        self.interrupt = True

    def tick(self):
        self.running = True
        fraction = self.progress_bar.get_fraction()
        new_val = self.on_tick(fraction)
        if new_val >= 1.0:
            self.progress_bar.set_fraction(1.0)
            self.on_complete()
            return False
        elif new_val == fraction:
            self.progress_bar.pulse()
        else:
            self.progress_bar.set_fraction(new_val)

        if self.interrupt:
            self.running = False
            self.on_interrupted()
            return False
        return True

    def on_close(self, w, tab):
        if self.timer:
            if self.running:
                gobject.source_remove(self.timer)
                self.running = False

        CloseTab.on_close(self, w, tab)

    def on_complete(self):
        pass

    def on_interrupted(self):
        pass

    def on_tick(self, fraction):
        return fraction

class SimProgressBarTab(ProgressBarTab):

    def __init__(self, title, simulator, window):
        ProgressBarTab.__init__(self, title)
        self.simulator = simulator
        self.win = window
        self.pack_start(self._create_content_panel(), False, False)
        self.simulator.connect("end_simulation", lambda s: self.stop())

    def _create_content_panel(self):
        vbox = gtk.VBox()
        vbox.pack_start(gtk.Label("Simulation progress"), False, False)
        vbox.pack_start(self.progress_bar, False, False)
        vbox.show_all()
        return vbox

    def on_complete(self):
        self.set_progressbar_text("Simulation completed...Gathering statistics")
        gtk.main_iteration()
        self.win.create_tab(PlotTab(self.get_title(), self.simulator))
        self.on_close(self, self)

    def on_interrupted(self):
        self.on_complete()

    def on_tick(self, fraction):
        values = self.simulator.graph.nodes.values()
        nodes_count = len(values)
        curr_count = 0
        for node in values:
            if node.is_discovered():
                curr_count += 1

        self.set_progressbar_text("{0}/{1}".format(curr_count, nodes_count))
        new_val = curr_count / float(nodes_count)
        return new_val

    def on_close(self, w, tab):
        if self.simulator.is_running():
            self.simulator.stop()
        ProgressBarTab.on_close(self, w, tab)

class PlotTab(CloseTab):
    def __init__(self, title, simulator):
        CloseTab.__init__(self, title)
        self.widget = plot.SimPlotWidget(simulator)
        self.pack_start(self.widget)

    def on_close(self, w, tab):
        self.widget.close()
        CloseTab.on_close(self, w, tab)