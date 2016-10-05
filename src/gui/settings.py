import paths
import os
import gtk
import gladeloader as gl
from misc import utils
from xml.etree.cElementTree import Element, SubElement, parse
from pango import FontDescription
from gui.events import EventSource

WINDOW_TITLE = "Process checker"
VERSION = "2.0"

CONFIG_FILENAME = "settings.cfg"
WINDOW_HEIGHT_MIN = 480
WINDOW_WIDTH_MIN = 640
WINDOW_HEIGHT_MAX = 1080
WINDOW_WIDTH_MAX = 1920
CONSOLE_HEIGHT_MIN = 10
CONSOLE_HEIGHT_MAX = WINDOW_HEIGHT_MAX - CONSOLE_HEIGHT_MIN
VIZ_SIMULATION_TIMER_MIN = 100
VIZ_SIMULATION_TIMER_MAX = 5000
MAX_VISIBLE_GRAPH_NODES_MIN = 1
MAX_VISIBLE_GRAPH_NODES_MAX = 2000

#default settings
VIZ_SIMULATION_TIMER_DEF = 1000
MAX_VISIBLE_GRAPH_NODES_DEF = 400
CONSOLE_FONT_DEF = "Calibri 14"
CONSOLE_HEIGHT_DEF = 100
WINDOW_WIDTH_DEF = 1280
WINDOW_HEIGHT_DEF = 720

#editable by user via config file
user_settings = { "VIZ_SIMULATION_TIMER": VIZ_SIMULATION_TIMER_DEF,
                  "MAX_VISIBLE_GRAPH_NODES": MAX_VISIBLE_GRAPH_NODES_DEF,
                  "CONSOLE_FONT": CONSOLE_FONT_DEF,
                  "CONSOLE_HEIGHT": CONSOLE_HEIGHT_DEF,
                  "WINDOW_WIDTH": WINDOW_WIDTH_DEF,
                  "WINDOW_HEIGHT": WINDOW_HEIGHT_DEF
                  }

def init():
    config_file = get_config_file()
    if config_file_exists():
        _load_settings(config_file)
    else:
        _save_settings(config_file)

def get_config_file():
    return os.path.join(paths.CONFIG_FILE_PATH, CONFIG_FILENAME)

def config_file_exists():
    return os.path.exists(get_config_file())

def _load_settings(config_filename):
        tree = parse(config_filename);
        root = tree.getroot()
        if root.get("version") != VERSION:
            raise Exception("Invalid version of settings file")
        sets_list = root.findall("set")
        for set in sets_list:
            key = set.get("name")
            val = set.get("value")
            is_value = True
            try:
                val = int(val)
            except Exception:
                is_value = False

            if key not in user_settings:
                raise Exception("Unknown settings " + key)

            if is_value:
                if key + "_MAX" in globals():
                    max_val = globals()[key + "_MAX"]
                    if val > max_val:
                        raise Exception("Value " + key + " is bigger then max value")
                if key + "_MIN" in globals():
                    min_val = globals()[key + "_MIN"]
                    if val < min_val:
                        raise Exception("Value " + key + " is smaller then min value")
            user_settings[key] = val

def _save_settings(config_filename):
        root = Element("settings")
        root.set("name", WINDOW_TITLE)
        root.set("version", VERSION)
        for k, v in user_settings.iteritems():
            set_elem = SubElement(root, "set")
            set_elem.set("name", str(k))
            set_elem.set("value", str(v))

        settings_data = utils.get_pretty_xml(root)
        with open(config_filename, "w") as f:
            f.write(settings_data)
            f.flush()

def get(settings_name):
    if settings_name in user_settings:
        return user_settings[settings_name]
    raise Exception("Unknown setting key")


class SettingPage(EventSource):
    def __init__(self, page_name):
        EventSource.__init__(self)
        self.register_event("apply")
        self.register_event("restore")
        self.page_name = page_name

    def apply(self):
        self.on_apply()
        self.commit()
        self.fire("apply")

    def restore(self):
        self.on_restore()
        self.commit()
        self.fire("restore")

    def on_apply(self):
        pass

    def on_restore(self):
        pass

    def commit(self):
        _save_settings(get_config_file())

    def get_page_name(self):
        return self.page_name

    def create_page(self, page_content):
        builder = gl.GladeLoader("settings_page").load()
        vbox = builder.get_object("vbox")
        title_label = builder.get_object("title_label")
        title_label.set_text(self.get_page_name())
        content_vbox = builder.get_object("content_vbox")
        content_vbox.pack_start(page_content)
        apply_button = builder.get_object("apply_button")
        restore_button = builder.get_object("restore_button")
        apply_button.connect("clicked", lambda w: self.apply())
        restore_button.connect("clicked", lambda w: self.restore())
        return vbox

    def build(self):
        page_content = self.build_page()
        return self.create_page(page_content)

    def build_page(self):
        pass

    def get_label(self):
        return gtk.Label(self.get_page_name())

class GeneralSettingPage(SettingPage):
    def __init__(self):
        SettingPage.__init__(self, "General")

    def build_page(self):
        builder = gl.GladeLoader("general_settings_page").load()
        vbox = builder.get_object("vbox")
        self.window_width_spin = builder.get_object("window_w_spin")
        self.window_height_spin = builder.get_object("window_h_spin")
        self.console_height_spin = builder.get_object("console_h_spin")
        self.font_entry = builder.get_object("font_entry")
        self.font_entry.set_text(get("CONSOLE_FONT"))

        self.window_width_spin.set_adjustment(gtk.Adjustment(get("WINDOW_WIDTH"),
                                                WINDOW_WIDTH_MIN,
                                                WINDOW_WIDTH_MAX,
                                                1,
                                                10))
        self.window_height_spin.set_adjustment(gtk.Adjustment(get("WINDOW_HEIGHT"),
                                                 WINDOW_HEIGHT_MIN,
                                                 WINDOW_HEIGHT_MAX,
                                                 1,
                                                 10))
        self.console_height_spin.set_adjustment(gtk.Adjustment(get("CONSOLE_HEIGHT"),
                                                  CONSOLE_HEIGHT_MIN,
                                                  CONSOLE_HEIGHT_MAX,
                                                  1,
                                                  10))
        return vbox

    def on_apply(self):
        window_width = self.window_width_spin.get_value_as_int()
        window_height = self.window_height_spin.get_value_as_int()
        console_height = self.console_height_spin.get_value_as_int()
        font = self.font_entry.get_text()
        if FontDescription(font):
            user_settings["CONSOLE_FONT"] = font
        user_settings["WINDOW_WIDTH"] = window_width
        user_settings["WINDOW_HEIGHT"] = window_height
        user_settings["CONSOLE_HEIGHT"] = console_height

    def on_restore(self):
        self.window_width_spin.set_value(WINDOW_WIDTH_DEF)
        self.window_height_spin.set_value(WINDOW_HEIGHT_DEF)
        self.console_height_spin.set_value(CONSOLE_HEIGHT_DEF)
        self.font_entry.set_text(CONSOLE_FONT_DEF)

        user_settings["CONSOLE_FONT"] = CONSOLE_FONT_DEF
        user_settings["WINDOW_WIDTH"] = WINDOW_WIDTH_DEF
        user_settings["WINDOW_HEIGHT"] = WINDOW_HEIGHT_DEF
        user_settings["CONSOLE_HEIGHT"] = CONSOLE_HEIGHT_DEF

class SimulationSettingPage(SettingPage):
    def __init__(self):
        SettingPage.__init__(self, "Simulation")

    def build_page(self):
        return gtk.VBox()

class VisualSimSettingPage(SettingPage):
    def __init__(self):
        SettingPage.__init__(self, "Visual simulation")

    def build_page(self):
        builder = gl.GladeLoader("vis_sim_settings_page").load()
        vbox = builder.get_object("vbox")
        self.sim_timer_spin = builder.get_object("sim_timer_spin")
        self.nodes_spin = builder.get_object("nodes_spin")
        self.sim_timer_spin.set_adjustment(gtk.Adjustment(get("VIZ_SIMULATION_TIMER"),
                                                VIZ_SIMULATION_TIMER_MIN,
                                                VIZ_SIMULATION_TIMER_MAX,
                                                1,
                                                10))
        self.nodes_spin.set_adjustment(gtk.Adjustment(get("MAX_VISIBLE_GRAPH_NODES"),
                                                 MAX_VISIBLE_GRAPH_NODES_MIN,
                                                 MAX_VISIBLE_GRAPH_NODES_MAX,
                                                 1,
                                                 10))
        return vbox

    def on_apply(self):
        sim_timer = self.sim_timer_spin.get_value_as_int()
        nodes_count = self.nodes_spin.get_value_as_int()
        user_settings["VIZ_SIMULATION_TIMER"] = sim_timer
        user_settings["MAX_VISIBLE_GRAPH_NODES"] = nodes_count

    def on_restore(self):
        self.sim_timer_spin.set_value(VIZ_SIMULATION_TIMER_DEF)
        self.nodes_spin.set_value(MAX_VISIBLE_GRAPH_NODES_DEF)

        user_settings["VIZ_SIMULATION_TIMER"] = VIZ_SIMULATION_TIMER_DEF
        user_settings["MAX_VISIBLE_GRAPH_NODES"] = MAX_VISIBLE_GRAPH_NODES_DEF
