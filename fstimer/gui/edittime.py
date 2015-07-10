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
'''Handling of the window dedicated to editing a single time entry'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import fstimer.gui
from fstimer.gui.GtkStockButton import GtkStockButton

class EditTimeWin(Gtk.Window):
    '''Handling of the window dedicated to editing a single time entry'''

    def __init__(self, timewin, old_id, old_time, clickedok_cb):
        '''Builds and display the window for editing a single time'''
        super(EditTimeWin, self).__init__(Gtk.WindowType.TOPLEVEL)
        self.timewin = timewin
        self.clickedok_cb = clickedok_cb
        self.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        self.set_transient_for(timewin)
        self.set_modal(True)
        self.set_title('fsTimer - Edit time')
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(20)
        self.connect('delete_event', lambda b, jnk: self.hide())
        label0 = Gtk.Label(label='')
        label0.set_markup('<span color="red">WARNING: Changes to these values cannot be automatically undone</span>\nIf you change the time and forget the old one, it will be gone forever.')
        label1 = Gtk.Label(label='ID:')
        self.entryid = Gtk.Entry()
        self.entryid.set_max_length(6)
        self.entryid.set_text(old_id)
        hbox1 = Gtk.HBox(False, 10)
        hbox1.pack_start(label1, False, False, 0)
        hbox1.pack_start(self.entryid, False, False, 0)
        label2 = Gtk.Label(label='Time:')
        self.entrytime = Gtk.Entry()
        self.entrytime.set_max_length(25)
        self.entrytime.set_text(old_time)
        hbox2 = Gtk.HBox(False, 10)
        hbox2.pack_start(label2, False, False, 0)
        hbox2.pack_start(self.entrytime, False, False, 0)
        btnOK = GtkStockButton(Gtk.STOCK_OK,"OK")
        btnOK.connect('clicked', self.winedittimeOK)
        btnCANCEL = GtkStockButton(Gtk.STOCK_CANCEL,"Cancel")
        btnCANCEL.connect('clicked', lambda b: self.hide())
        cancel_algn = Gtk.Alignment.new(0, 0, 0, 0)
        cancel_algn.add(btnCANCEL)
        hbox3 = Gtk.HBox(False, 10)
        hbox3.pack_start(cancel_algn, True, True, 0)
        hbox3.pack_start(btnOK, False, False, 0)
        vbox = Gtk.VBox(False, 10)
        vbox.pack_start(label0, False, False, 10)
        vbox.pack_start(hbox1, False, False, 0)
        vbox.pack_start(hbox2, False, False, 0)
        vbox.pack_start(hbox3, False, False, 0)
        self.add(vbox)
        self.show_all()

    def winedittimeOK(self, jnk_unused):
        '''Handles click on OK button
           Stores times that have been modified'''
        new_id = self.entryid.get_text()
        new_time = self.entrytime.get_text()
        self.clickedok_cb(new_id, new_time)
