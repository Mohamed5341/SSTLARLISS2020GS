import serial
import serial.tools.list_ports_linux as ports
import gi.repository.GLib as gobject
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("cairo", "1.0")
from gi.repository import Gtk, Gdk
from gi.repository import cairo

import math
import gc
import re



class MyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self,title="Serial Print")
        self.connected_dev = None;
        self.connected = False;
        self.angle=0
        
        self.set_default_size(600,450)

        grid = Gtk.Grid()

        self.devices = Gtk.ListStore(str, str)

        self.combo = Gtk.ComboBox.new_with_model_and_entry(self.devices)

        self.dara = Gtk.DrawingArea()

        self.load_devices()

        renderer = Gtk.CellRendererText()

        self.combo.pack_start(renderer, True)
        self.combo.add_attribute(renderer, 'text', 0)
        self.combo.set_entry_text_column(1)
        self.combo.connect("changed",self.on_chose_from_combo)

        self.button = Gtk.Button.new_with_label("Connect")
        self.button2 = Gtk.Button.new_with_label("Disconnect")
        self.button.connect("clicked", self.click_connect)
        self.button2.connect("clicked", self.click_disconnect)
        

        self.button2.set_sensitive(False)

        self.dara.set_size_request(300,300)

        self.dara.connect("draw",self.on_draw,[0.96,0.94,0.26])

        grid.attach(self.combo,0,0,7,2)
        grid.attach(self.button,7,0,4,1)
        grid.attach(self.button2,7,1,4,1)
        grid.attach(self.dara,0,2,11,11)

        self.dara.set_hexpand(True)
        self.dara.set_vexpand(True)

        self.add(grid)

    def on_chose_from_combo(self, combo):
        itr = combo.get_active_iter()
        model = combo.get_model()
        if model[itr][0] == "Search":
            self.load_devices()
            
        
    def load_devices(self):
        self.devices = Gtk.ListStore(str, str)
        lis = ports.comports()
        for port in lis:
            self.devices.append([port.device, port.manufacturer])
        self.devices.append(["Search","None"])
        self.combo.set_model(self.devices)
        self.connected_dev = None

    def update_draw(self):
        while self.connected_dev.in_waiting:
            line =self.connected_dev.readline().decode("utf-8")
            matchObj = re.match( r'IMU,(.*)', line)
            if matchObj:
                self.angle=float(matchObj.group(1))
                self.dara.queue_draw()
            print(line,end='')
        return self.connected

    def click_connect(self, widget):
        itr = self.combo.get_active_iter()
        model = self.combo.get_model()
        if itr == None:
            print(f'Select Valid device')
            return

        selected = model[itr][0]
        
        for port in ports.comports():
            if(port.device == selected):
                self.connected_dev = serial.Serial(selected)
                self.connected = True;
                self.button.set_sensitive(False)
                self.button2.set_sensitive(True)
                self.combo.set_sensitive(False)
                gobject.timeout_add(50, self.update_draw)

                return
        print(f'{selected} is not connected device')

    def click_disconnect(self, widget):
        self.connected = False
        self.button.set_sensitive(True)
        self.button2.set_sensitive(False)
        self.combo.set_sensitive(True)


    def on_draw(self,widget,cr,color):
        # get the width and height of the drawing area
        w = self.dara.get_allocated_width()
        h = self.dara.get_allocated_height()

        # move to the center of the drawing area
        # (translate from the top left corner to w/2, h/2)
        cr.translate(w / 2, h / 2)

        if abs(self.angle)>(math.pi/36):
            #rotate axis
            cr.rotate(self.angle)
        cr.rectangle(-50, -50, 100, 100)
        cr.set_source_rgb(color[0], color[1], color[2])
        cr.fill()

        return True

window = MyWindow()        
window.show_all()
window.connect("destroy", Gtk.main_quit)

Gtk.main()
