import paths
import os
import ntpath
import gtk
import sys
import gladeloader as gl
from simulator.misc import utils
from xml.etree.cElementTree import Element, SubElement, parse
from pango import FontDescription
from events import EventSource
from simulator.sim import processfactory as pf
from dialogs import dialog

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
CANVAS_BACKGROUND_COLOR = "(247, 207, 45)"

#editable by user via config file
user_settings = { "VIZ_SIMULATION_TIMER": VIZ_SIMULATION_TIMER_DEF,
                  "MAX_VISIBLE_GRAPH_NODES": MAX_VISIBLE_GRAPH_NODES_DEF,
                  "CONSOLE_FONT": CONSOLE_FONT_DEF,
                  "CONSOLE_HEIGHT": CONSOLE_HEIGHT_DEF,
                  "WINDOW_WIDTH": WINDOW_WIDTH_DEF,
                  "WINDOW_HEIGHT": WINDOW_HEIGHT_DEF,
                  "CANVAS_BACKGROUND_COLOR": CANVAS_BACKGROUND_COLOR
                  }

default_scripts = []
user_scripts = []

def init():
    config_file = get_config_file()
    if config_file_exists():
        try:
            _load_settings(config_file)
        except Exception as ex:
            err_msg = "Config file load error: {0}".format(ex.message)
            print err_msg
            sys.exit(1)
    else:
        _save_settings(config_file)

def get_config_file():
    return os.path.join(paths.CONFIG_FILE_PATH, CONFIG_FILENAME)

def config_file_exists():
    return os.path.exists(get_config_file())

def _load_settings(config_filename):
        tree = parse(config_filename)
        root = tree.getroot()
        if root.get("version") != VERSION:
            raise Exception("Invalid version of settings file")
        sets_list = root.findall("set")
        for s in sets_list:
            key = s.get("name")
            val = s.get("value")
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

        #check if color string is correct. Exception is raised if is invalid.
        utils.color_from_string(get("CANVAS_BACKGROUND_COLOR"))

        scripts_el = root.find("scripts")
        for script_el in scripts_el.findall("script"):
            script_path = script_el.get("value")
            if os.path.exists(script_path):
                try:
                    pf.process_factory.load_from_script(script_path)
                except Exception as ex:
                    print ex.message

def _save_settings(config_filename):
        root = Element("settings")
        root.set("name", WINDOW_TITLE)
        root.set("version", VERSION)
        for k, v in user_settings.iteritems():
            set_elem = SubElement(root, "set")
            set_elem.set("name", str(k))
            set_elem.set("value", str(v))
        scripts_el = SubElement(root, "scripts")
        for s in user_scripts:
            script_el = SubElement(scripts_el, "script")
            script_el.set("name", ntpath.basename(s))
            script_el.set("value", s)
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
        self.color_box = builder.get_object("color_box")
        def_color = get("CANVAS_BACKGROUND_COLOR")
        color = utils.color_from_string(def_color)
        self.color = gtk.gdk.color_parse(utils.rgb_to_hex(*color))
        self.color_box.modify_bg(gtk.STATE_NORMAL, self.color)
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
        self.color_button = builder.get_object("pick_color_button")
        self.color_button.connect("clicked", self.on_pick_color_button_clicked)
        return vbox

    def on_apply(self):
        sim_timer = self.sim_timer_spin.get_value_as_int()
        nodes_count = self.nodes_spin.get_value_as_int()
        user_settings["VIZ_SIMULATION_TIMER"] = sim_timer
        user_settings["MAX_VISIBLE_GRAPH_NODES"] = nodes_count
        user_settings["CANVAS_BACKGROUND_COLOR"] = utils.color_to_string(self.color)

    def on_restore(self):
        self.sim_timer_spin.set_value(VIZ_SIMULATION_TIMER_DEF)
        self.nodes_spin.set_value(MAX_VISIBLE_GRAPH_NODES_DEF)

        user_settings["VIZ_SIMULATION_TIMER"] = VIZ_SIMULATION_TIMER_DEF
        user_settings["MAX_VISIBLE_GRAPH_NODES"] = MAX_VISIBLE_GRAPH_NODES_DEF
        user_settings["CANVAS_BACKGROUND_COLOR"] = CANVAS_BACKGROUND_COLOR

    def on_pick_color_button_clicked(self, button):
        color_selection = gtk.ColorSelectionDialog("Pick color")
        result = color_selection.run()
        if result == gtk.RESPONSE_OK:
            selected_color = color_selection.colorsel.get_current_color()
            self.color_box.modify_bg(gtk.STATE_NORMAL, selected_color)
            self.color = (selected_color.red / 256,
                          selected_color.green / 256,
                          selected_color.blue / 256)

        color_selection.destroy()


class ScriptSettingPage(SettingPage):
    def __init__(self):
        SettingPage.__init__(self, "Scripts")

    def build_page(self):
        builder = gl.GladeLoader("scripts_settings_page").load()
        vbox = builder.get_object("vbox")
        self.liststore = builder.get_object("liststore")
        self.treeview = builder.get_object("treeview")
        self.add_button = builder.get_object("add_button")
        self.remove_button = builder.get_object("remove_button")
        self.add_button.connect("clicked", self.on_add_script)
        self.remove_button.connect("clicked", self.on_remove_script)
        self._load_scripts()
        return vbox

    def on_apply(self):
        scripts_paths = pf.process_factory.get_scripts()
        global user_scripts
        user_scripts = scripts_paths

    def on_restore(self):
        pf.process_factory.clear_scripts()
        self.liststore.clear()
        global default_scripts
        global user_scripts
        user_scripts = default_scripts

    def on_add_script(self, w):
        python_script = dialog.PythonDialogFactory().open("Load script")
        if python_script:
            try:
                pf.process_factory.load_from_script(python_script)
                self._load_scripts()
            except (SystemExit, Exception) as ex:
                print ex

    def on_remove_script(self, w):
        i = self._get_selected_row_iter()
        if i:
            script_path = self.liststore[i][1]
            pf.process_factory.remove_script(script_path)
            self.liststore.remove(i)

    def _load_scripts(self):
        self.liststore.clear()
        for script in pf.process_factory.get_scripts():
            self.liststore.append([ntpath.basename(script), script])

    def _get_selected_row_iter(self):
        tree_selection = self.treeview.get_selection()
        if tree_selection:
            model, rows = tree_selection.get_selected_rows()
            if model and rows:
                if len(rows):
                    return model.get_iter(rows[0][0])
        return None

