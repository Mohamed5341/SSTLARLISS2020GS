# import required libraries
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

def button_click(a):
    print("clicked")

#Adding more than one widget needs box to contain widgets

#create VBox (vertical box)
container = Gtk.VBox()

#create Entry
entry = Gtk.Entry()

#add placeholder text
entry.set_placeholder_text("Enter Name")

#set Entry width
entry.set_width_chars(30)

#create label
label = Gtk.Label()
label.set_markup('<span size="larger">Hi, ...</span>')

#create button
button = Gtk.Button.new_with_label("Enter")

#set on click event
button.connect("clicked", button_click)

#add label and entry to box
container.pack_start(label,False,False,50)
container.pack_start(entry,False,False,0)
container.pack_start(button,False,False,0)


#create window
window = Gtk.Window(title="Forum")

#add Box to window
window.add(container)

#change window default size as it will become so small
window.set_default_size(600,450)

#you need to use show_all to show window content also
#using show only will show window without label
window.show_all()

#focus on button
button.grab_focus()

window.connect("destroy", Gtk.main_quit)
Gtk.main()

