import gtk

class MultiSimulationDialog():
    DEFAULT_PROCESS_COUNT = 0
    MAX_PROCESS_COUNT = 32

    def __init__(self, window, processes_types):
        self.dialog = gtk.Dialog(title = "Simulation properties", parent = window, buttons = (gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_APPLY,
                                        gtk.RESPONSE_OK))

        self.dialog.set_default_response(gtk.RESPONSE_OK)
        self.dialog.set_default_size(200, 200)
        self.liststore = gtk.ListStore(str, bool, int)
        for process_type in processes_types:
            self.liststore.append([process_type, False, 0])

        treeview = gtk.TreeView(model = self.liststore)
        
        text_renderer = gtk.CellRendererText()
        text_column = gtk.TreeViewColumn("Process type", text_renderer, text = 0)
        treeview.append_column(text_column)

        toggle_renderer = gtk.CellRendererToggle()
        toggle_column = gtk.TreeViewColumn("Enabled", toggle_renderer, active = 1)
        toggle_renderer.connect("toggled", self.on_toggled)
        treeview.append_column(toggle_column)

        adj = gtk.Adjustment(self.DEFAULT_PROCESS_COUNT, self.DEFAULT_PROCESS_COUNT, self.MAX_PROCESS_COUNT, 1)
        spiner_renderer = gtk.CellRendererSpin()
        spiner_renderer.connect("edited", self.on_spin_edited)
        spiner_renderer.set_property("editable", True)
        spiner_renderer.set_property("adjustment", adj)
        spinner_column = gtk.TreeViewColumn("Process count", spiner_renderer, text = 2)
        treeview.append_column(spinner_column)
        
        adj = gtk.Adjustment(1, 1, 100, 1)
        self.spinner = gtk.SpinButton(adj)
        self.spinner.set_numeric(True)
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("Simulations count"), False, False)
        hbox.pack_start(self.spinner)
        self.dialog.vbox.pack_start(treeview)
        self.dialog.vbox.pack_start(hbox)
        self.dialog.vbox.show_all()

    def on_toggled(self, w, path):
        self.liststore[path][1] = not self.liststore[path][1]

    def on_spin_edited(self, w, path, value):
        self.liststore[path][2] = int(value)

    def get_data(self):
        count = self.spinner.get_value_as_int()
        p = []
        for item in self.liststore:
            if item[1] and item[2] > 0:
                p.append((item[0], item[2]))
        return (count, p)

    def run(self):
        return self.dialog.run()

    def destroy(self):
        self.dialog.destroy()
