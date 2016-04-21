import gtk

class CSVDialog():
    TITLE_OPEN = "Open csv file"
    TITLE_WRITE = "Save csv file"

    @staticmethod
    def open_file():
        dialog = gtk.FileChooserDialog(CSVDialog.TITLE_OPEN,
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_OPEN,
                                       (gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN,
                                        gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_folder("./")
        xml_file_filter = gtk.FileFilter()
        xml_file_filter.set_name("Csv files")
        xml_file_filter.add_pattern("*.csv")
        dialog.set_filter(xml_file_filter)
        try:
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                return dialog.get_file()
            return None
        finally:
            dialog.destroy()

    @staticmethod
    def save_as_file():
        dialog = gtk.FileChooserDialog(CSVDialog.TITLE_WRITE,
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE,
                                        gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_folder("./")
        xml_file_filter = gtk.FileFilter()
        xml_file_filter.set_name("Csv files")
        xml_file_filter.add_pattern("*.csv")
        dialog.set_filter(xml_file_filter)
        try:
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                return dialog.get_file()
            return None
        finally:
            dialog.destroy()

    @staticmethod
    def save_file(file):
        dialog = gtk.FileChooserDialog(CSVDialog.TITLE_WRITE,
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL,
                                        gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE,
                                        gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_file(file)
        try:
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                    new_file = dialog.get_file()
                    with open(file.get_path(), "r") as old_f:
                        with open(new_file.get_path(), "w") as new_f:
                            for line in old_f:
                                new_f.write(line)
                            new_f.flush()
                    return True
            return False
        except IOError as ioex:
            print ioex.message
            return False
        finally:
            dialog.destroy()
