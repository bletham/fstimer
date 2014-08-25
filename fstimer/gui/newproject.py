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

    def __init__(self, define_fields_cb, parent):
        '''Creates new project window'''
        super(NewProjectWin, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.define_fields_cb = define_fields_cb
        self.modify_bg(gtk.STATE_NORMAL, fstimer.gui.bgcolor)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title('fsTimer - New project')
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_border_width(20)
        self.connect('delete_event', lambda b, jnk_unused: self.hide())
        ##Now create the vbox.
        vbox = gtk.VBox(False, 10)
        self.add(vbox)
        ##Now add the text.
        label_0 = gtk.Label('Enter a name for the new project.\nOnly letters, numbers, and underscore.')
        ##And an error, if needed..
        label_1 = gtk.Label()
        label_1.set_line_wrap(True)
        ##And the text entry
        entry = gtk.Entry(max=32)
        ##And an hbox with 2 buttons
        hbox = gtk.HBox(False, 0)
        btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
        btnCANCEL.connect('clicked', lambda btn: self.hide())
        alignCANCEL = gtk.Alignment(0, 0, 0, 0)
        alignCANCEL.add(btnCANCEL)
        btnNEXT = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        btnNEXT.connect('clicked', self.nextClicked, entry, label_1)
        alignNEXT = gtk.Alignment(1, 0, 1, 0)
        alignNEXT.add(btnNEXT)
        entry.connect("changed", self.lock_btn_title, entry, btnNEXT)
        btnNEXT.set_sensitive(False)
        ##And populate
        hbox.pack_start(alignCANCEL, True, True, 0)
        hbox.pack_start(alignNEXT, False, False, 0)
        vbox.pack_start(label_0, False, False, 0)
        vbox.pack_start(entry, False, False, 0)
        vbox.pack_start(label_1, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)
        self.show_all()

    def lock_btn_title(self, jnk_unused, entry, btnNEXT):
        '''locks btnNEXT if the project name doesn't mean specifications'''
        txt = entry.get_text()
        if not txt or re.search('[^a-zA-Z0-9_]+', txt):
            btnNEXT.set_sensitive(False)
        else:
            btnNEXT.set_sensitive(True)
        return

    def nextClicked(self, jnk_unused, entry, label):
        '''handles click on next by checking new project name
           and calling back fsTimer'''
        entry_text = str(entry.get_text())
        if os.path.exists(entry_text):
            # Add the error text.
            label.set_markup('<span color="red">Error! File or directory named "'+entry_text+'" already exists. Try again.</span>')
            label.show()
        else:
            label.set_markup('')
            self.hide()
            self.define_fields_cb(entry_text+'/')
