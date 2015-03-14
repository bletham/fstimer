#fsTimer - free, open source software for race timing.
#Copyright 2012-14 Ben Letham

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

#The author/copyright holder can be contacted at bletham@gmail.com
'''Handling of the window used for editing t0, the race start time'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import fstimer.gui

class EditT0Win(Gtk.Window):
    '''Handling of the window used for editing t0, the race start time'''

    def __init__(self, path, parent, t0, okclicked_cb):
        '''Builds and display the edit t0 window'''
        super(EditT0Win, self).__init__(Gtk.WindowType.TOPLEVEL)
        self.okclicked_cb = okclicked_cb
        self.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        self.set_title('fsTimer - ' + path)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.connect('delete_event', lambda b, jnk: self.hide())
        label = Gtk.Label("""This is the starting time in seconds.\
            \nAdd or subtract seconds from this number to adjust the start time by that many seconds.\
            \nNote that this will NOT affect times that have already been marked, only future times.""")
        self.t0box = Gtk.Entry()
        self.t0box.set_text(str(t0))
        hbox = Gtk.HBox(False, 8)
        btnOK = Gtk.Button(stock=Gtk.STOCK_OK)
        btnOK.connect('clicked', self.okclicked)
        btnCANCEL = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        btnCANCEL.connect('clicked', lambda jnk: self.hide())
        hbox.pack_start(btnOK, False, False, 0)
        hbox.pack_start(btnCANCEL, False, False, 0)
        hbox_lbl = Gtk.HBox(False, 0)
        hbox_lbl.pack_start(label, False, False, 10)
        vbox = Gtk.VBox(False, 8)
        vbox.pack_start(hbox_lbl, False, False, 20)
        vbox.pack_start(self.t0box, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)
        self.add(vbox)
        self.show_all()

    def okclicked(self, jnk_unused):
        '''Handles click on OK button'''
        self.okclicked_cb(float(self.t0box.get_text()))
