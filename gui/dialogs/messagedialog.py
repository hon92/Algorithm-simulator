import gtk

class MessageDialog():
    def _create_message_dialog(self, parent, dtype, text):
        msg_dialog = gtk.MessageDialog(parent,
                                       gtk.DIALOG_DESTROY_WITH_PARENT,
                                       type = dtype,
                                       buttons = gtk.BUTTONS_OK)
        msg_dialog.set_markup(text)
        hbox = msg_dialog.vbox.get_children()[1]
        button_ok = hbox.get_children()[0] 
        button_ok.connect("activate", lambda w: msg_dialog.destroy())
        button_ok.connect("clicked", lambda w: msg_dialog.destroy())
        return msg_dialog

    def info_dialog(self, parent, text):
        self._create_message_dialog(parent, gtk.MESSAGE_INFO, text).run()

    def error_dialog(self, parent, text):
        self._create_message_dialog(parent, gtk.MESSAGE_ERROR, text).run()