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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import fstimer.gui
from fstimer.gui.GtkStockButton import GtkStockButton

class FamilyResetWin(Gtk.Window):
    '''Handling of the window dedicated to the definition of the field
       to reset when registering several members of a family'''

    def __init__(self, fields, clear_for_fam, back_clicked_cb, next_clicked_cb, parent):
        '''Creates family reset window'''
        super(FamilyResetWin, self).__init__(Gtk.WindowType.TOPLEVEL)
        self.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title('fsTimer - Family reset')
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(20)
        self.connect('delete_event', lambda b, jnk: self.hide())
        # Now create the vbox.
        vbox = Gtk.VBox(False, 2)
        self.add(vbox)
        # Now add the text.
        label1_0 = Gtk.Label("Choose the fields to clear when adding a new family member.\nPress 'Forward' to continue with the default settings, or make edits below.")
        vbox.pack_start(label1_0, False, False, 0)
        btnlist = []
        for field in fields:
            btnlist.append(Gtk.CheckButton(field))
            if field in clear_for_fam:
                btnlist[-1].set_active(True)
            else:
                btnlist[-1].set_active(False)
            vbox.pack_start(btnlist[-1], True, True, 0)
        # And an hbox with 2 buttons
        hbox = Gtk.HBox(False, 0)
        btnCANCEL = GtkStockButton(Gtk.STOCK_CANCEL,"Cancel")
        btnCANCEL.connect('clicked', lambda btn: self.hide())
        alignCANCEL = Gtk.Alignment.new(0, 0, 0, 0)
        alignCANCEL.add(btnCANCEL)
        btnBACK = GtkStockButton(Gtk.STOCK_GO_BACK,"Back")
        btnBACK.connect('clicked', back_clicked_cb)
        btnNEXT = GtkStockButton(Gtk.STOCK_GO_FORWARD,"Next")
        btnNEXT.connect('clicked', next_clicked_cb, btnlist)
        ##And populate
        hbox.pack_start(alignCANCEL, True, True, 0)
        hbox.pack_start(btnBACK, False, False, 2)
        hbox.pack_start(btnNEXT, False, False, 0)
        vbox.pack_start(hbox, False, False, 8)
        self.show_all()
