import gtk
import tab

class Window(gtk.Window):
    def __init__(self, app):
        gtk.Window.__init__(self)
        self.app = app
        self._create_window()

    def _create_notebook(self):
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_TOP)
        return self.notebook

    def _create_window(self):
        self.set_title("Process checker")
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_size_request(640, 480)
        self.connect("destroy", self.close)

        vbox = gtk.VBox()
        self.add(vbox)
        vbox.pack_start(self._create_menu(), False, False)
        vbox.pack_start(self._create_notebook())
        self.create_tab(tab.WelcomeTab("Welcome tab"))

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
            icons_path = "../resources/icons/"
            image.set_from_file(icons_path + image_name)
            image.show()
            item.set_image(image)
            item.connect("activate", lambda w: callback())
            parent_menu.append(item)
        
        file_menu = add_menu("File")        
        add_image_menu_item(file_menu, "Open project", self.app.open_project, "Open Folder-24.png")
        #add_image_menu_item(file_menu, "Save project", self.app.save_project, "Save-24.png")
        add_image_menu_item(file_menu, "Close project", self.app.close_project, "Close Window-24.png")
        add_image_menu_item(file_menu, "Settings", self.app.open_settings, "Settings-24.png")
        add_image_menu_item(file_menu, "Exit", self.app.close, "Exit-24.png")

        simulation_menu = add_menu("Simulation")
        add_image_menu_item(simulation_menu, "Run", self.app.start_simulation, "Play-24.png")
        add_image_menu_item(simulation_menu, "Run graphics sim", self.app.start_graphics_simulation, "Flow Chart-24.png")
        return menu

    def create_tab(self, tab):
        if not tab:
            return
        self.notebook.append_page(tab, tab.get_tab_label())
        self.notebook.set_current_page(self.notebook.get_n_pages() - 1)
        tab.notebook = self.notebook
        if self.app.project:
            self.app.project.tabs.append(tab)
        return tab

    def show(self):
        self.show_all()
        
    def close(self, w):
        self.app.close()
      

