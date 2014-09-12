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
'''Handling of the window dedicated to the definition of the field
   to reset when registering several members of a family'''

import pygtk
pygtk.require('2.0')
import gtk
import fstimer.gui

class FamilyResetWin(gtk.Window):
    '''Handling of the window dedicated to the definition of the field
       to reset when registering several members of a family'''

    def __init__(self, fields, back_clicked_cb, next_clicked_cb, parent):
        '''Creates family reset window'''
        super(FamilyResetWin, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.modify_bg(gtk.STATE_NORMAL, fstimer.gui.bgcolor)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title('fsTimer - New project')
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_border_width(20)
        self.connect('delete_event', lambda b, jnk: self.hide())
        # Now create the vbox.
        vbox = gtk.VBox(False, 2)
        self.add(vbox)
        # Now add the text.
        label1_0 = gtk.Label("Choose the fields to clear when adding a new family member.\nPress 'Forward' to continue with the default settings, or make edits below.")
        vbox.pack_start(label1_0, False, False, 0)
        btnlist = []
        for field in fields:
            btnlist.append(gtk.CheckButton(field))
            if field in ['First name', 'Gender', 'Age', 'ID', 'Handicap']:
                btnlist[-1].set_active(True)
            else:
                btnlist[-1].set_active(False)
            vbox.pack_start(btnlist[-1])
        # And an hbox with 2 buttons
        hbox = gtk.HBox(False, 0)
        btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
        btnCANCEL.connect('clicked', lambda btn: self.hide())
        alignCANCEL = gtk.Alignment(0, 0, 0, 0)
        alignCANCEL.add(btnCANCEL)
        btnBACK = gtk.Button(stock=gtk.STOCK_GO_BACK)
        btnBACK.connect('clicked', back_clicked_cb)
        btnNEXT = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        btnNEXT.connect('clicked', next_clicked_cb, btnlist)
        ##And populate
        hbox.pack_start(alignCANCEL, True, True, 0)
        hbox.pack_start(btnBACK, False, False, 2)
        hbox.pack_start(btnNEXT, False, False, 0)
        vbox.pack_start(hbox, False, False, 8)
        self.show_all()
