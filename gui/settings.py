import paths
import os
from misc import utils
from xml.etree.cElementTree import Element, SubElement, parse
from xml.etree import ElementTree

WINDOW_TITLE = "Process checker"
VERSION = "1.0"

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

#editable by user via config file
user_settings = { "VIZ_SIMULATION_TIMER": 1000,
                  "MAX_VISIBLE_GRAPH_NODES": 400,
                  "CONSOLE_FONT": "Calibri 14",
                  "CONSOLE_HEIGHT": 100,
                  "WINDOW_WIDTH": 1280,
                  "WINDOW_HEIGHT": 720
                  }

def init():
    config_file = os.path.join(paths.ROOT, CONFIG_FILENAME)
    if not os.path.exists(config_file):
        _save_settings(config_file)
    else:
        _load_settings(config_file)
        print "loaded settings"

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
        try:
            root = Element("settings")
            root.set("name", WINDOW_TITLE)
            root.set("version", VERSION)
            for k, v in user_settings.iteritems():
                set_elem = SubElement(root, "set")
                set_elem.set("name", str(k))
                set_elem.set("value", str(v))

            with open(config_filename, "w") as f:
                f.write(utils.get_pretty_xml(root))
                f.flush()
            return True
        except Exception as ex:
            return False

def get(settings_name):
    if settings_name in user_settings:
        return user_settings[settings_name]
    raise Exception("Unknown setting key")
