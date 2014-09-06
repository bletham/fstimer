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

import pygtk
pygtk.require('2.0')
import gtk
import fstimer.gui

class EditT0Win(gtk.Window):
    '''Handling of the window used for editing t0, the race start time'''

    def __init__(self, path, parent, t0, okclicked_cb):
        '''Builds and display the edit t0 window'''
        super(EditT0Win, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.okclicked_cb = okclicked_cb
        self.modify_bg(gtk.STATE_NORMAL, fstimer.gui.bgcolor)
        self.set_title('fsTimer - ' + path)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.connect('delete_event', lambda b, jnk: self.hide())
        self.t0box = gtk.Entry()
        self.t0box.set_text(str(t0))
        hbox = gtk.HBox(False, 8)
        btnOK = gtk.Button(stock=gtk.STOCK_OK)
        btnOK.connect('clicked', self.okclicked)
        btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
        btnCANCEL.connect('clicked', lambda jnk: self.hide())
        hbox.pack_start(btnOK, False, False, 8)
        hbox.pack_start(btnCANCEL, False, False, 8)
        vbox = gtk.VBox(False, 8)
        vbox.pack_start(self.t0box, False, False, 8)
        vbox.pack_start(hbox, False, False, 8)
        self.add(vbox)
        self.show_all()

    def okclicked(self, jnk_unused):
        '''Handles click on OK button'''
        self.okclicked_cb(float(self.t0box.get_text()))
