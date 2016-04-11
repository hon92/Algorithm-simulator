import gtk

class SimulationDialog():
    DEFAULT_PROCESS_COUNT = 1
    MAX_PROCESS_COUNT = 32

    def __init__(self, window, processor_types):
        self.dialog = gtk.Dialog(title = "Simulation properties", parent = window, buttons = (gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_APPLY,
                                        gtk.RESPONSE_OK))

        self.dialog.set_default_response(gtk.RESPONSE_OK)
        adj = gtk.Adjustment(self.DEFAULT_PROCESS_COUNT, self.DEFAULT_PROCESS_COUNT, self.MAX_PROCESS_COUNT, 1)
        self.spinner = gtk.SpinButton(adj)
        self.spinner.set_numeric(True)
        self.combobox = gtk.combo_box_new_text()
        for t in processor_types:
            self.combobox.append_text(t)
        self.combobox.set_active(0)
        self.dialog.vbox.pack_start(self._create_dialog(), False, False)

    def _create_dialog(self):
        table = gtk.Table(2, 2, False)
        table.attach(gtk.Label("Process count"), 0, 1, 0, 1)
        table.attach(self.spinner, 1, 2, 0, 1)
        table.attach(gtk.Label("Process type"), 0, 1, 1, 2)
        table.attach(self.combobox, 1, 2, 1, 2)
        table.show_all()
        return table

    def get_process_count(self):
        return self.spinner.get_value_as_int();

    def get_process_type(self):
        return self.combobox.get_active_text()

    def run(self):
        return self.dialog.run()

    def destroy(self):
        self.dialog.destroy()