import gtk
import paths

class Dialog():
    @staticmethod
    def get_factory(factory_type):
        if factory_type == "xml":
            return XmlDialogFactory()
        elif factory_type == "csv":
            return CsvDialogFactory()
        elif factory_type == "txt":
            return TxtDialogFactory()
        else:
            raise Exception("Invalid factory type")

class DialogFactory():
    def open(self, title = None):
        pass

    def save(self, title = None, text = None):
        pass

    def save_as(self, title = None, text = None):
        pass

    def response(self, dialog):
        pass

class XmlDialogFactory(DialogFactory):
    def create_xml_filter(self):
        xml_file_filter = gtk.FileFilter()
        xml_file_filter.set_name("Xml files")
        xml_file_filter.add_pattern("*.xml")
        return xml_file_filter

    def response(self, dialog):
        try:
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                filename = dialog.get_filename()
                if filename:
                    if filename.endswith(".xml"):
                        return filename
                    else:
                        return filename + ".xml"
                return filename
            else:
                return None
        finally:
            dialog.destroy()

    def open(self, title = None):
        if not title:
            title = "Open xml file"

        dialog = gtk.FileChooserDialog(title,
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_OPEN,
                                       (gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN,
                                        gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_folder(paths.ROOT)
        dialog.set_filter(self.create_xml_filter())
        return self.response(dialog)

    def save(self, title = None, text = None):
        if not title:
            title = "Save xml file"
        if not text:
            text = ""

        dialog = gtk.FileChooserDialog(title,
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE,
                                        gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_folder(paths.ROOT)
        dialog.set_current_name(text)
        dialog.set_filter(self.create_xml_filter())
        return self.response(dialog)

    def save_as(self, title = None, text = None):
        if not title:
            title = "Save as xml file"
        if not text:
            text = ".xml"

        return self.save(title, text)

class CsvDialogFactory(DialogFactory):
    def create_csv_filter(self):
        csv_file_filter = gtk.FileFilter()
        csv_file_filter.set_name("Csv files")
        csv_file_filter.add_pattern("*.csv")
        return csv_file_filter

    def response(self, dialog):
        try:
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                filename = dialog.get_filename()
                if filename:
                    if filename.endswith(".csv"):
                        return filename
                    else:
                        return filename + ".csv"
                return filename
            else:
                return None
        finally:
            dialog.destroy()

    def open(self, title = None):
        if not title:
            title = "Open csv file"

        dialog = gtk.FileChooserDialog(title,
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_OPEN,
                                       (gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN,
                                        gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_folder(paths.ROOT)
        dialog.set_filter(self.create_csv_filter())
        return self.response(dialog)

    def save(self, title = None, text = None):
        if not title:
            title = "Save csv file"
        if not text:
            text = ""

        dialog = gtk.FileChooserDialog(title,
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE,
                                        gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_folder(paths.ROOT)
        dialog.set_current_name(text)
        dialog.set_filter(self.create_csv_filter())
        return self.response(dialog)

    def save_as(self, title = None, text = None):
        if not title:
            title = "Save as csv file"
        if not text:
            text = ".csv"

        return self.save(title, text)

class TxtDialogFactory(DialogFactory):
    def create_txt_filter(self):
        txt_file_filter = gtk.FileFilter()
        txt_file_filter.set_name("Txt files")
        txt_file_filter.add_pattern("*.txt")
        return txt_file_filter

    def response(self, dialog):
        try:
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                filename = dialog.get_filename()
                if filename:
                    if filename.endswith(".txt"):
                        return filename
                    else:
                        return filename + ".txt"
                return filename
            else:
                return None
        finally:
            dialog.destroy()

    def open(self, title = None):
        if not title:
            title = "Open txt file"

        dialog = gtk.FileChooserDialog(title,
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_OPEN,
                                       (gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN,
                                        gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_folder(paths.ROOT)
        dialog.set_filter(self.create_txt_filter())
        return self.response(dialog)

    def save(self, title = None, text = None):
        if not title:
            title = "Save txt file"
        if not text:
            text = ""

        dialog = gtk.FileChooserDialog(title,
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE,
                                        gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_folder(paths.ROOT)
        dialog.set_current_name(text)
        dialog.set_filter(self.create_txt_filter())
        return self.response(dialog)

    def save_as(self, title = None, text = None):
        if not title:
            title = "Save as txt file"
        if not text:
            text = ".txt"

        return self.save(title, text)

class InputDialog(gtk.Dialog):
    def __init__(self, title, parent):
        gtk.Dialog.__init__(self, title,
                            parent,
                            flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            buttons = (gtk.STOCK_CANCEL,
                                       gtk.RESPONSE_REJECT,
                                       gtk.STOCK_OK,
                                       gtk.RESPONSE_ACCEPT))
        self.entry = gtk.Entry()
        self.entry.connect("activate", lambda w: self.response(gtk.RESPONSE_ACCEPT))
        self.vbox.pack_start(self.entry, False, False)
        self.set_default_response(gtk.RESPONSE_ACCEPT)
        self.show_all()

    def run(self):
        try:
            val = gtk.Dialog.run(self)
            text = None
            if val == gtk.RESPONSE_ACCEPT:
                text = self.entry.get_text()
            return text
        finally:
            self.destroy()

