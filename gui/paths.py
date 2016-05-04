import os
import sys

GUI_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(GUI_PATH)
RESOURCES = os.path.join(ROOT, "resources")
ICONS_PATH = os.path.join(RESOURCES, "icons", "")
GLADE_DIALOG_DIRECTORY = os.path.join(GUI_PATH, "dialogs", "glade_dialogs", "")

if sys.platform == "win32":
    DOT_DIRECTORY = "C:\\Program Files (x86)\\Graphviz2.38\\bin\\"
    DOT_PROGRAM = "dot.exe"
    DOT_CMD_STRING = "\"" + DOT_DIRECTORY + DOT_PROGRAM + "\""
elif sys.platform == "linux2":
    DOT_DIRECTORY = ""
    DOT_PROGRAM = "dot"
    DOT_CMD_STRING = DOT_PROGRAM 