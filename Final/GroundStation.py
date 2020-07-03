import serial
import serial.tools.list_ports_linux as ports
import gi.repository.GLib as gobject
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("cairo", "1.0")
from gi.repository import Gtk as gtk
from gi.repository import Gdk
from gi.repository import cairo
from gi.repository import GdkPixbuf

import pytopo.MapWindow as MapWindow
import pytopo.MapViewer as MapViewer
import pytopo.TrackPoints as TrackPoints

import gc
import re


#create class to window which is inherite from MapWindow
class MyMapWindow(MapWindow):

    #override __init__ method
    def __init__(self,_controller):
        #call default constructor then add new widgets
        MapWindow.__init__(self,_controller)

        #create widgets        
        ad = gtk.Adjustment(value=15,lower=2,upper=19,step_increment=1,page_increment=0,page_size=0)

        self.spin = gtk.SpinButton(adjustment=ad, climb_rate=1, digits=0)

        self.connected_dev = None;
        self.connected = False;
        self.started = False;
        self.angle=0

        self.devices = gtk.ListStore(str, str)
        self.renderer = gtk.CellRendererText()
        self.grid = gtk.Grid()
        self.devices_combo = gtk.ComboBox.new_with_model_and_entry(self.devices)
        self.connect_button = gtk.Button.new_with_label("Connect")
        self.disconnect_button = gtk.Button.new_with_label("Disconnect")

        self.trackpoints = TrackPoints()

        self.img = GdkPixbuf.Pixbuf.new_from_file("rover.svg")

        #drawing area for rover image
        self.dare = gtk.DrawingArea()

        
        

    #override show window
    def show_window(self, init_width, init_height):
        #create window        
        win = gtk.Window()
        #change window title        
        win.set_name("Ground Station")      
        win.connect("destroy", self.graceful_exit)
        win.set_border_width(5)
        
        
        win.add(self.grid)

        self.load_devices()

        self.dare.set_size_request(300,300)

        self.devices_combo.pack_start(self.renderer, True)
        self.devices_combo.add_attribute(self.renderer, 'text', 0)
        self.devices_combo.set_entry_text_column(1)
        self.devices_combo.connect("changed",self.on_chose_from_combo)


        #drawing area for map
        self.drawing_area = gtk.DrawingArea()

        self.connect_button.connect("clicked", self.click_connect)
        self.disconnect_button.connect("clicked", self.click_disconnect)
        self.dare.connect("draw",self.on_draw)
        self.disconnect_button.set_sensitive(False)

        
        self.grid.attach(self.drawing_area,0,0,50,50)
        self.grid.attach(self.dare,50,0,20,20)
        self.grid.attach(self.devices_combo,50,46,20,1)
        self.grid.attach(self.spin,50,47,20,1)
        self.grid.attach(self.connect_button,50,48,20,1)
        self.grid.attach(self.disconnect_button,50,49,20,1)
        

        

        #make widget fill window
        self.drawing_area.set_vexpand(True)
        self.drawing_area.set_hexpand(True)
        self.devices_combo.set_vexpand(False)
        self.devices_combo.set_hexpand(False)


        #this part is the same as in library
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

    
    #override this function to start from specified location
    def selection_window(self):
        #manual beginning site
        site = ['Home', 31.121302, 30.018407, 'Wikimedia', 15]#wikimedia
	
        self.controller.use_site(site, self)
        return;        
        


    #this function is called when data is recived
    def get_data(self):
        while self.connected_dev.in_waiting:
            line =self.connected_dev.readline().decode("utf-8")
            #check if it is GPS            
            if line[0:3] == "GPS":
                matchObj = re.match( r'GPS,(.*),(.*),(.*),(.*),(.*),(.*),(.*),', line)
                if matchObj:
                    time = float(matchObj.group(1))
                    latitude = float(matchObj.group(2))
                    ns = str(matchObj.group(3))
                    longitude = float(matchObj.group(4))
                    ew = str(matchObj.group(5))
                    print(time, latitude, ns, longitude, ew)
                    self.collection.zoom_to(self.spin.get_value_as_int() ,self.center_lat)
                    self.pin_lon = float(longitude)
                    self.pin_lat = float(latitude)
                    if(self.started):
                        self.trackpoints.handle_track_point(lat=latitude,lon=longitude)
                    else:
                        self.trackpoints.handle_track_point(lat=latitude, lon=longitude, waypoint_name="start")
                        self.trackpoints.handle_track_point(lat=latitude,lon=longitude)
                        self.started = True
                    self.draw_map()
                    self.draw_trackpoints()
                else:
                    print(line,end='')
            #check if it is IMU
            elif line[0:3] == "IMU":
                matchObj = re.match( r'IMU,(.*)', line)
                if matchObj:
                    self.angle=float(matchObj.group(1))
                    self.dare.queue_draw()
                print(line,end='')
        return self.connected
      

    #this function is called when you change your selection from combobox
    def on_chose_from_combo(self, combo):
        itr = combo.get_active_iter()
        model = combo.get_model()
        if model[itr][0] == "Search":
            self.load_devices()
            
        
    #this function is used to load Connected serial devices
    def load_devices(self):
        self.devices = gtk.ListStore(str, str)
        lis = ports.comports()
        for port in lis:
            self.devices.append([port.device, port.manufacturer])
        self.devices.append(["Search","None"])
        self.devices_combo.set_model(self.devices)
        self.connected_dev = None


    #it is called when connect button is clicked
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
                gobject.timeout_add(50, self.get_data)

                return
        print(f'{selected} is not connected device')


    #it is called when disconnect button is clicked
    def click_disconnect(self, widget):
        self.connected = False
        self.connect_button.set_sensitive(True)
        self.disconnect_button.set_sensitive(False)
        self.devices_combo.set_sensitive(True)


    #it is called when rover drawing area is created
    def on_draw(self,widget,cr):
        # get the width and height of the drawing area
        w = self.dare.get_allocated_width()
        h = self.dare.get_allocated_height()

        # move to the center of the drawing area
        # (translate from the top left corner to w/2, h/2)
        cr.translate(w / 2, h / 2)
        cr.rotate(self.angle)

        #add image to cr (cairo.Context object)
        Gdk.cairo_set_source_pixbuf(cr,self.img,-133,-100)
        cr.paint()

        return True



#create class to view window in addition to load data
class MyViewer(MapViewer):
    def main(self):
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


viewer = MyViewer()
viewer.main()
