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
'''Handling of the new project windows'''

import pygtk
pygtk.require('2.0')
import gtk
import os, re
import fstimer.gui

class NewProjectWin(gtk.Window):
    '''Handles the creation of a new project'''

    def __init__(self, set_projecttype_cb, parent):
        '''Creates new project window'''
        super(NewProjectWin, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.modify_bg(gtk.STATE_NORMAL, fstimer.gui.bgcolor)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title('fsTimer - New project')
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_border_width(20)
        self.connect('delete_event', lambda b, jnk_unused: self.hide())
        # Now create the vbox.
        vbox = gtk.VBox(False, 10)
        self.add(vbox)
        # Now add the text.
        label_0 = gtk.Label('Enter a name for the new project.\nOnly letters, numbers, and underscore.')
        # And an error, if needed..
        self.label_1 = gtk.Label()
        self.label_1.set_line_wrap(True)
        # And the text entry
        self.entry = gtk.Entry(max=32)
        # And an hbox with 2 buttons
        hbox_1 = gtk.HBox(False, 0)
        btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
        btnCANCEL.connect('clicked', lambda btn: self.hide())
        alignCANCEL = gtk.Alignment(0, 0, 0, 0)
        alignCANCEL.add(btnCANCEL)
        btnNEXT = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        btnNEXT.connect('clicked', self.nextClicked, set_projecttype_cb)
        alignNEXT = gtk.Alignment(1, 0, 1, 0)
        alignNEXT.add(btnNEXT)
        btnNEXT.set_sensitive(False)
        # And populate
        self.entry.connect("changed", self.lock_btn_title, btnNEXT)
        hbox_1.pack_start(alignCANCEL, True, True, 0)
        hbox_1.pack_start(alignNEXT, False, False, 0)
        vbox.pack_start(label_0, False, False, 0)
        vbox.pack_start(self.entry, False, False, 0)
        vbox.pack_start(self.label_1, False, False, 0)
        vbox.pack_start(hbox_1, False, False, 0)
        self.show_all()

    def lock_btn_title(self, jnk_unused, btnNEXT):
        '''locks btnNEXT if the project name doesn't meet specifications'''
        txt = self.entry.get_text()
        btnNEXT.set_sensitive((len(txt) > 0) and \
                              (not re.search('[^a-zA-Z0-9_]+', txt)))
        return

    def nextClicked(self, jnk_unused, set_projecttype_cb):
        '''handles click on next by checking new project name
           and calling back fsTimer'''
        entry_text = str(self.entry.get_text())
        if os.path.exists(entry_text):
            # Add the error text.
            self.label_1.set_markup('<span color="red">Error! File or directory named "'+entry_text+'" already exists. Try again.</span>')
            self.label_1.show()
        else:
            self.label_1.set_markup('')
            self.hide()
            set_projecttype_cb(entry_text)
