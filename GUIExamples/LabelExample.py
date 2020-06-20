# import required libraries
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


#create label
label = Gtk.Label()

#add text to label
label.set_text("Hello, World!")


#create window
window = Gtk.Window(title="Label")

#add label to window
window.add(label)


#change window default size as it will become so small
window.set_default_size(600,450)

#you need to use show_all to show window content also
#using show only will show window without label
window.show_all()
window.connect("destroy", Gtk.main_quit)
Gtk.main()
