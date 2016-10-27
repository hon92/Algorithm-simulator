import gtk
import pango
import paths
import settings
from gui.dialogs import dialog


class Window(gtk.Window):
    def __init__(self, app):
        gtk.Window.__init__(self)
        self.app = app
        self.console = Console()
        self._create_window()

    def _create_notebook(self):
        self.notebook = gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.set_tab_pos(gtk.POS_TOP)
        return self.notebook

    def _create_window(self):
        self.set_title("")
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_size_request(settings.get("WINDOW_WIDTH"),
                              settings.get("WINDOW_HEIGHT"))
        self.connect("destroy", self.close)

        vbox = gtk.VBox()
        self.add(vbox)
        vbox.pack_start(self._create_menu(), False, False)
        vpaned = gtk.VPaned()
        vpaned.pack1(self._create_notebook(), True, False)
        vpaned.pack2(self.console, False, False)
        vbox.pack_start(vpaned)

    def _create_menu(self):
        menu = gtk.MenuBar()

        def add_menu(label):
            m = gtk.Menu()
            item = gtk.MenuItem(label)
            item.set_submenu(m)
            menu.append(item)
            return m

        def add_menu_item(parent_menu, label, callback):
            item = gtk.MenuItem(label)
            item.connect("activate", lambda w: callback())
            parent_menu.append(item)

        def add_image_menu_item(parent_menu, label, callback, image_name):
            item = gtk.ImageMenuItem(label)
            image = gtk.Image()
            icons_path = paths.ICONS_PATH
            image.set_from_file(icons_path + image_name)
            image.show()
            item.set_image(image)
            item.connect("activate", lambda w: callback())
            parent_menu.append(item)

        file_menu = add_menu("File")
        add_image_menu_item(file_menu, "Create project", self.app.create_project, "Create New-24.png")
        add_image_menu_item(file_menu, "Open project", self.app.open_project, "Open Folder-24.png")
        add_image_menu_item(file_menu, "Save project", self.app.save_project, "Save-24.png")
        add_image_menu_item(file_menu, "Close project", self.app.close_project, "Close Window-24.png")
        add_image_menu_item(file_menu, "Settings", self.app.open_settings, "Settings-24.png")
        add_image_menu_item(file_menu, "Exit", self.app.close, "Exit-24.png")

        simulation_menu = add_menu("Simulation")
        add_image_menu_item(simulation_menu, "Run", self.app.start_simulation, "Play-24.png")
        add_image_menu_item(simulation_menu, "Run graphics sim", self.app.start_graphics_simulation, "Flow Chart-24.png")

        generation_menu = add_menu("Generate")
        add_image_menu_item(generation_menu, "Graph", self.app.generate_graph, "Flow Chart-24.png")
        return menu

    def set_title(self, text):
        if text:
            title = "{0} {1} '{2}'".format(settings.WINDOW_TITLE,
                                           settings.VERSION,
                                           text)
        else:
            title = "{0} {1}".format(settings.WINDOW_TITLE,
                                     settings.VERSION)
        return gtk.Window.set_title(self, title)

    def create_tab(self, tab):
        tab.create()
        self.notebook.append_page(tab, tab.get_tab_label())
        self.notebook.set_menu_label_text(tab, tab.get_title())
        self.notebook.set_current_page(self.notebook.get_n_pages() - 1)
        if self.app.project and not tab.is_project_independent():
            self.app.project.add_tab(tab)
        return tab

    def remove_tab(self, tab):
        page_number = self.notebook.page_num(tab)
        if page_number != -1:
            if self.app.project:
                self.app.project.remove_tab(tab)
            self.notebook.remove_page(page_number)
            tab.destroy()
            del tab

    def get_tab(self, name):
        for i in xrange(self.notebook.get_n_pages()):
            tab = self.notebook.get_nth_page(i)
            if tab.get_title() == name:
                return tab
        return None

    def get_tab_at_pos(self, position):
        if position < 0 or position >= self.notebook.get_n_pages():
            return None
        return self.notebook.get_nth_page(position)

    def switch_to_tab(self, tab):
        pos = self.notebook.page_num(tab)
        if pos != -1:
            self.notebook.set_current_page(pos)

    def show(self):
        self.show_all()

    def close(self, w):
        self.app.close()


class Console(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self)
        self.buffer = gtk.TextBuffer()
        self.textview = gtk.TextView(self.buffer)
        font = pango.FontDescription(settings.get("CONSOLE_FONT"))
        self.textview.modify_font(font)
        self.textview.set_editable(False)
        self.buffer.create_tag("out", foreground = "black")
        self.buffer.create_tag("err", foreground = "red")
        self.buffer.create_tag("warn", foreground = "yellow")
        self._create_content()

    def _create_content(self):
        def create_button(icon, tooltip, callback):
            button = gtk.Button()
            image = gtk.Image()
            image.set_from_file(paths.ICONS_PATH + icon)
            button.add(image)
            button.set_tooltip_text(tooltip)
            button.connect("clicked", lambda w: callback())
            button.show_all()
            return button

        clear_button = create_button("Delete-24 (1).png",
                                          "Clear console",
                                          self.clear)
        export_button = create_button("exit.png",
                                      "Export text from console",
                                      self.export)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.add(self.textview)
        self.pack_start(sw)
        vbox = gtk.VBox()
        vbox.pack_start(clear_button, False, False)
        vbox.pack_start(export_button, False, False)
        self.pack_start(vbox, False, False)
        self.set_size_request(-1, settings.get("CONSOLE_HEIGHT"))

    def _write_to_buffer(self, text, tag, scroll_end = True):
        self.buffer.insert_with_tags_by_name(self.buffer.get_end_iter(),
                                             text,
                                             tag)
        if scroll_end:
            self.scroll_to_end()

    def write(self, text, tag = "out"):
        self._write_to_buffer(text, tag)

    def writeln(self, text, tag = "out"):
        self.write(text + "\n", tag)

    def clear(self):
        self.buffer.set_text("")

    def get_text(self):
        si = self.buffer.get_start_iter()
        ei = self.buffer.get_end_iter()
        return self.buffer.get_text(si, ei)

    def export(self):
        text = self.get_text()
        if text:
            filename = dialog.Dialog.get_factory("txt").save_as("Save to file")
            if filename:
                with open(filename, "w") as f:
                    f.write(text)
                    f.flush()
                self.writeln("Console text exported to '{0}'".format(filename))

    def scroll_to_end(self):
        self.textview.scroll_mark_onscreen(self.buffer.get_insert())

