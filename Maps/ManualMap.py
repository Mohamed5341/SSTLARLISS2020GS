import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk as gtk

import pytopo.MapWindow as MapWindow
import pytopo.MapViewer as MapViewer

import gc


class MyMapWindow(MapWindow):

    #override init
    def __init__(self, _controller):
        MapWindow.__init__(self, _controller)

        ad = gtk.Adjustment(value=15,lower=2,upper=19,step_increment=1,page_increment=0,page_size=0)

        self.go_button = gtk.Button.new_with_label("Go")
        self.lon_entry = gtk.Entry()
        self.lat_entry = gtk.Entry()
        self.spin = gtk.SpinButton(adjustment=ad, climb_rate=1, digits=0)


    #override show window
    def show_window(self, init_width, init_height):
        """Create the initial window."""
        win = gtk.Window()
        win.set_name("Ground Station")
        win.connect("destroy", self.graceful_exit)
        win.set_border_width(5)
        

        grid = gtk.Grid()
        win.add(grid)

        self.drawing_area = gtk.DrawingArea()
        # There doesn't seem to be any way to resize a window below
        # the initial size of the drawing area. So make the drawing area
        # initially tiny, then just before showing we'll resize the window.
        # self.drawing_area.size(10, 10)
        grid.attach(self.drawing_area,0,0,50,50)
        grid.attach(self.lat_entry,50,1,1,1)
        grid.attach(self.lon_entry,50,2,1,1)
        grid.attach(self.spin,50,3,1,1)
        grid.attach(self.go_button,50,4,1,1)


        #make widget fill window
        self.go_button.set_hexpand(True)
        self.lat_entry.set_hexpand(True)
        self.drawing_area.set_vexpand(True)
        self.drawing_area.set_hexpand(True)
        self.go_button.set_vexpand(False)


        #change entry shapes
        self.lat_entry.set_width_chars(10)
        self.lon_entry.set_width_chars(10)
        self.lat_entry.set_placeholder_text("Latitude")
        self.lon_entry.set_placeholder_text("Longitude")

        
        #set click event for button click
        self.go_button.connect("clicked", self.go_to_location)


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

        # The default focus in/out handlers on drawing area cause
        # spurious expose events.  Trap the focus events, to block that:
        # XXX can we pass "pass" in to .connect?
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
    def go_to_location(self, widget):
        self.collection.zoom_to(self.spin.get_value_as_int() ,self.center_lat)
        self.center_lon = float(self.lon_entry.get_text())
        self.center_lat = float(self.lat_entry.get_text())
        self.pin_lon = float(self.lon_entry.get_text())
        self.pin_lat = float(self.lat_entry.get_text())
        self.draw_map()
      



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
       

        # For cProfile testing, run with a dummy collection (no data needed):
        # mapwin.collection = MapCollection("dummy", "/tmp")

        # print(cProfile.__file__)
        # cProfile.run('mapwin.show_window()', 'cprof.out')
        # http://docs.python.org/library/profile.html
        # To analyze cprof.out output, do this:
        # import pstats
        # p = pstats.Stats('fooprof')
        # p.sort_stats('time').print_stats(20)

        mapwin.show_window(self.init_width, self.init_height)




viewer = MyMapViewer()
viewer.main()
