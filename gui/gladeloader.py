import gtk
import paths

class GladeLoader():
    def __init__(self, glade_filename):
        self.glade_filename = glade_filename
        self.full_name = paths.GLADE_DIALOG_DIRECTORY + glade_filename + ".glade"

    def load(self):
        builder = gtk.Builder()
        builder.add_from_file(self.full_name)
        return builder
