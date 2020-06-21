import serial
import serial.tools.list_ports_linux as ports
import gi.repository.GLib as gobject
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class MyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self,title="Serial Print")
        self.connected_dev = None;
        self.connected = False;
        
        self.set_default_size(600,450)

        grid = Gtk.Grid()

        self.devices = Gtk.ListStore(str, str)

        self.combo = Gtk.ComboBox.new_with_model_and_entry(self.devices)

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
        self.entry = Gtk.Entry()
        label_frame = Gtk.Frame()
        label_frame.set_label("Output")

        self.entry.set_text("This is Output")
        self.button2.set_sensitive(False)


        label_frame.add(self.entry)
        grid.attach(self.combo,0,0,7,2)
        grid.attach(self.button,7,0,4,1)
        grid.attach(self.button2,7,1,4,1)
        grid.attach(label_frame,0,2,11,11)

        label_frame.set_vexpand(True)
        label_frame.set_hexpand(True)

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

    def update_label(self):
        while self.connected_dev.in_waiting:
            line =self.connected_dev.readline().decode("utf-8") 
            print(line)
            self.entry.set_text(line)
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
                gobject.timeout_add(50, self.update_label)

                return
        print(f'{selected} is not connected device')

    def click_disconnect(self, widget):
        self.connected = False
        self.button.set_sensitive(True)
        self.button2.set_sensitive(False)
        self.combo.set_sensitive(True)


window = MyWindow()        
window.show_all()
window.connect("destroy", Gtk.main_quit)

Gtk.main()

