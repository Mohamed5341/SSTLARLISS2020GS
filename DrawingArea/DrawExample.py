import gi
gi.require_version("Gtk", "3.0")
gi.require_version("cairo", "1.0")
from gi.repository import Gtk, Gdk
from gi.repository import cairo

import math


class MyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self,title="Drawing Area")
        self.set_default_size(600,450)

        self.angle=45

        self.grid = Gtk.Grid()
        self.adjs = Gtk.Adjustment(value=self.angle,lower=0,upper=360,step_increment=1,page_increment=0,page_size=0)
        self.spin = Gtk.SpinButton(adjustment=self.adjs,climb_rate=1,digits=0)
        self.dara = Gtk.DrawingArea()

        self.dara.set_size_request(300,300)

        self.dara.connect("draw",self.on_draw,[0.96,0.94,0.26])
        self.spin.connect("value-changed", self.get_angle)

        self.grid.attach(self.spin,0,0,1,1)
        self.grid.attach(self.dara,0,1,1,1)

        self.spin.set_hexpand(True)
        self.spin.set_vexpand(False)
        self.dara.set_hexpand(True)
        self.dara.set_vexpand(True)


        self.add(self.grid)

    def get_angle(self,widget):
        self.angle = self.spin.get_value_as_int()
        # redraw what is in the drawing area
        self.dara.queue_draw()

    def on_draw(self,widget,cr,color):
        # get the width and height of the drawing area
        w = self.dara.get_allocated_width()
        h = self.dara.get_allocated_height()

        # move to the center of the drawing area
        # (translate from the top left corner to w/2, h/2)
        cr.translate(w / 2, h / 2)

        #rotate axis
        cr.rotate(self.angle*math.pi/180)
        cr.rectangle(-50, -50, 100, 100)
        cr.set_source_rgb(color[0], color[1], color[2])
        cr.fill()

        return True
        


win = MyWindow()
win.show_all()
win.connect("destroy", Gtk.main_quit)
Gtk.main()
