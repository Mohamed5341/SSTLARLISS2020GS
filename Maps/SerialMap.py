import serial
import serial.tools.list_ports_linux as ports
import gi.repository.GLib as gobject
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk as gtk
import pytopo.MapWindow as MapWindow
import pytopo.MapViewer as MapViewer
import gc
import re


class MyMapWindow(MapWindow):

    #override init
    def __init__(self, _controller):
        MapWindow.__init__(self, _controller)

        ad = gtk.Adjustment(value=15,lower=2,upper=19,step_increment=1,page_increment=0,page_size=0)

        self.spin = gtk.SpinButton(adjustment=ad, climb_rate=1, digits=0)
        self.connected_dev = None;
        self.connected = False;

        self.devices = gtk.ListStore(str, str)
        self.renderer = gtk.CellRendererText()
        self.grid = gtk.Grid()
        self.devices_combo = gtk.ComboBox.new_with_model_and_entry(self.devices)
        self.connect_button = gtk.Button.new_with_label("Connect")
        self.disconnect_button = gtk.Button.new_with_label("Disconnect")


    #override show window
    def show_window(self, init_width, init_height):
        """Create the initial window."""
        win = gtk.Window()
        win.set_name("Ground Station")
        win.connect("destroy", self.graceful_exit)
        win.set_border_width(5)
        
        win.add(self.grid)

        self.load_devices()

        self.devices_combo.pack_start(self.renderer, True)
        self.devices_combo.add_attribute(self.renderer, 'text', 0)
        self.devices_combo.set_entry_text_column(1)
        self.devices_combo.connect("changed",self.on_chose_from_combo)

        self.connect_button.connect("clicked", self.click_connect)
        self.disconnect_button.connect("clicked", self.click_disconnect)
        self.disconnect_button.set_sensitive(False)

        self.drawing_area = gtk.DrawingArea()
        self.grid.attach(self.drawing_area,0,0,50,50)
        self.grid.attach(self.devices_combo,50,0,10,1)
        self.grid.attach(self.spin,50,1,10,1)
        self.grid.attach(self.connect_button,50,2,10,1)
        self.grid.attach(self.disconnect_button,50,3,10,1)

        #make widget fill window
        self.drawing_area.set_vexpand(True)
        self.drawing_area.set_hexpand(True)
        self.devices_combo.set_vexpand(False)
        self.devices_combo.set_hexpand(False)


        self.drawing_area.set_events(gtk.gdk.EXPOSURE_MASK |
                                     gtk.gdk.SCROLL_MASK |
                                     gtk.gdk.POINTER_MOTION_MASK |
                                     gtk.gdk.POINTER_MOTION_HINT_MASK |
                                     gtk.gdk.BUTTON_PRESS_MASK |
                                     gtk.gdk.BUTTON_RELEASE_MASK)

        try:
            # GTK2:
            self.drawing_area.connect("expose-event", self.expose_event)
        except TypeError:
            # Python3/GI GTK3:
            self.drawing_area.connect('size-allocate', self.on_size_allocate)
            self.width = self.height = 0
            self.drawing_area.connect('draw', self.expose3)

        self.drawing_area.connect("button-press-event",   self.mousepress)
        self.drawing_area.connect("button-release-event", self.mouserelease)
        self.drawing_area.connect("scroll-event",         self.scroll_event)
        self.drawing_area.connect("motion_notify_event",  self.drag_event)

        self.drawing_area.connect("focus-in-event", self.nop)
        self.drawing_area.connect("focus-out-event", self.nop)

        # Handle key presses on the drawing area.
        self.drawing_area.set_property('can-focus', True)
        self.drawing_area.connect("key-press-event", self.key_press_event)

        # Resize the window now to the desired initial size:
        win.resize(init_width, init_height)

        win.show_all()

        if self.gps_poller:
            gobject.threads_init()

        gtk.main()

    def selection_window(self):
        #manual beginning site
        site = ['Home', 31.121302, 30.018407, 'Wikimedia', 15]#wikimedia
	
        self.controller.use_site(site, self)
        return;        
        


    #this function is called when GO button is clicked 
    def go_to_location(self):
        while self.connected_dev.in_waiting:
            line =self.connected_dev.readline().decode("utf-8") 
            matchObj = re.match( r'GPS,(.*),(.*),(.*),(.*),(.*),(.*),(.*),', line)
            if matchObj:
                print(float(matchObj.group(1)), float(matchObj.group(2)), str(matchObj.group(3)), float(matchObj.group(4)), str(matchObj.group(5)))
                self.collection.zoom_to(self.spin.get_value_as_int() ,self.center_lat)
                self.pin_lon = float(matchObj.group(4))
                self.pin_lat = float(matchObj.group(2))
                self.draw_map()
            else:
                print(line)
        return self.connected
      

    def on_chose_from_combo(self, combo):
        itr = combo.get_active_iter()
        model = combo.get_model()
        if model[itr][0] == "Search":
            self.load_devices()
            
        
    def load_devices(self):
        self.devices = gtk.ListStore(str, str)
        lis = ports.comports()
        for port in lis:
            self.devices.append([port.device, port.manufacturer])
        self.devices.append(["Search","None"])
        self.devices_combo.set_model(self.devices)
        self.connected_dev = None


    def click_connect(self, widget):
        itr = self.devices_combo.get_active_iter()
        model = self.devices_combo.get_model()
        if itr == None:
            print(f'Select Valid device')
            return

        selected = model[itr][0]
        
        for port in ports.comports():
            if(port.device == selected):
                self.connected_dev = serial.Serial(selected)
                self.connected = True;
                self.connect_button.set_sensitive(False)
                self.disconnect_button.set_sensitive(True)
                self.devices_combo.set_sensitive(False)
                gobject.timeout_add(50, self.go_to_location)

                return
        print(f'{selected} is not connected device')

    def click_disconnect(self, widget):
        self.connected = False
        self.connect_button.set_sensitive(True)
        self.disconnect_button.set_sensitive(False)
        self.devices_combo.set_sensitive(True)



class MyMapViewer(MapViewer):
    def main(self):
        """main execution routine for pytopo."""
        self.exec_config_file()
        # Remember how many known sites we got from the config file;
        # the rest are read in from saved sites and may need to be re-saved.
        self.first_saved_site = len(self.KnownSites)

        # Now it's safe to read the saved sites.
        self.read_saved_sites()

        self.read_tracks()
        gc.enable()

        mapwin = MyMapWindow(self)

        mapwin.selection_window()

        mapwin.show_window(self.init_width, self.init_height)




viewer = MyMapViewer()
viewer.main()
