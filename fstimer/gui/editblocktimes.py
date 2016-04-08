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
'''Handling of the window used for editing a block of times'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import fstimer.gui
from fstimer.gui.util_classes import GtkStockButton

class EditBlockTimesWin(Gtk.Window):
    '''Handling of the window used for editing a block of times'''

    def __init__(self, parent, okclicked_cb):
        '''Builds and display the window for editing block of times'''
        super(EditBlockTimesWin, self).__init__(Gtk.WindowType.TOPLEVEL)
        self.okclicked_cb = okclicked_cb
        self.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title('fsTimer - Edit times')
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(20)
        self.connect('delete_event', lambda b, jnk: self.hide())
        label0 = Gtk.Label(label='')
        label0.set_markup('<span color="red">WARNING: Changes to times cannot be automatically undone</span>\nIf you change the times and forget the old values, they will be gone forever.')
        label1 = Gtk.Label(label='Time (h:mm:ss) to be added or subtracted from all selected times:')
        self.radiobutton = Gtk.RadioButton(group=None, label="ADD")
        self.radiobutton.set_active(True)
        radiobutton2 = Gtk.RadioButton(group=self.radiobutton, label="SUBTRACT")
        self.entrytime = Gtk.Entry()
        self.entrytime.set_max_length(7)
        self.entrytime.set_text('0:00:00')
        hbox1 = Gtk.HBox(False, 10)
        hbox1.pack_start(self.radiobutton, False, False, 0)
        hbox1.pack_start(radiobutton2, False, False, 0)
        hbox1.pack_start(self.entrytime, False, False, 0)
        btnOK = GtkStockButton('ok',"OK")
        btnOK.connect('clicked', self.okclicked)
        btnCANCEL = GtkStockButton('close',"Cancel")
        btnCANCEL.connect('clicked', lambda b: self.hide())
        cancel_algn = Gtk.Alignment.new(0, 0, 0, 0)
        cancel_algn.add(btnCANCEL)
        hbox2 = Gtk.HBox(False, 10)
        hbox2.pack_start(cancel_algn, True, True, 0)
        hbox2.pack_start(btnOK, False, False, 0)
        vbox = Gtk.VBox(False, 10)
        vbox.pack_start(label0, False, False, 10)
        vbox.pack_start(label1, False, False, 10)
        vbox.pack_start(hbox1, False, False, 0)
        vbox.pack_start(hbox2, False, False, 0)
        self.add(vbox)
        self.show_all()

    def okclicked(self, jnk_unused):
        '''Hancles click on the ok button'''
        operation = [r.get_label() for r in self.radiobutton.get_group()
                     if r.get_active()][0]
        self.okclicked_cb(operation, self.entrytime.get_text())
