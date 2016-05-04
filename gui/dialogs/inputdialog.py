import gtk

class InputDialog(gtk.Dialog):
    def __init__(self, title, parent):
        gtk.Dialog.__init__(self, title,
                            parent,
                            flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.entry = gtk.Entry()
        self.vbox.pack_start(self.entry, False, False)
        self.set_default_response(gtk.RESPONSE_ACCEPT)
        self.show_all()

    def run(self):
        val = gtk.Dialog.run(self)
        text = None
        if val == gtk.RESPONSE_ACCEPT:
            text = self.entry.get_text()
        self.destroy()
        return text