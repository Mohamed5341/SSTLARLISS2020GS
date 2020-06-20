import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


window = Gtk.Window(title="Grids")
window.set_default_size(600,450)
window.maximize()#maximize window


top_right = Gtk.Label()
top_left = Gtk.Label()
bottom = Gtk.Label()

#expanding one item inside grid will expand the whole item
bottom.set_hexpand(True)
bottom.set_vexpand(True)

top_right.set_text("Top Right")
top_left.set_text("Top Left")
bottom.set_text("Bottom")


#create Grid
grid = Gtk.Grid()

grid.set_column_spacing(1)


grid.attach(top_left,0,0,1,1)
grid.attach(top_right,1,0,1,1)
grid.attach_next_to(bottom, top_left, Gtk.PositionType.BOTTOM, 2, 1)


window.add(grid)

window.show_all()
window.connect("destroy", Gtk.main_quit)
Gtk.main()

