#fsTimer - free, open source software for race timing.
#Copyright 2012-15 Ben Letham

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
'''Handling of the introduction windows to select/create a project'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os
from os.path import normpath, join, dirname, abspath
import fstimer.gui
from fstimer.gui.util_classes import GtkStockButton

class IntroWin(Gtk.Window):
    '''Handles an introduction window to select/create a project'''

    def __init__(self, load_project_cb, create_project_cb):
        '''Builds and display the introduction window'''
        super(IntroWin, self).__init__(Gtk.WindowType.TOPLEVEL)
        self.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        icon_fname = normpath(join(dirname(abspath(__file__)),'../data/icon.png'))
        self.set_icon_from_file(icon_fname)
        self.set_title('fsTimer')
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(20)
        self.connect('delete_event', Gtk.main_quit)
        # Create the vbox that will contain everything
        vbox = Gtk.VBox(False, 10)
        self.add(vbox)
        # Main logo
        logo = Gtk.Image()
        logo.set_from_file(normpath(join(dirname(abspath(__file__)),'../data/fstimer_logo.png')))
        # Welcome text
        label0 = Gtk.Label(label='')
        label = Gtk.Label('Select an existing project, or begin a new project.')
        # A combobox to select the project
        combobox = Gtk.ComboBoxText()
        projectlist = [' -- Select an existing project --']
        rootdir = normpath(join(dirname(abspath(__file__)),'../../'))
        projectlist.extend([i for i in os.listdir(rootdir) if os.path.isdir(join(rootdir,i)) and os.path.exists(join(rootdir,i+'/'+i+'.reg'))]) #List the folders in pwd that contain a .reg registration file
        projectlist.sort()
        for project in projectlist:
            combobox.append_text(project)
        combobox.set_active(0)
        #An hbox for the buttons.
        hbox = Gtk.HBox(False, 0)
        #And build the buttons
        btnNEW = GtkStockButton('new','New')
        btnNEW.connect('clicked', create_project_cb)
        btnOK = GtkStockButton('ok','OK')
        btnOK.connect('clicked', load_project_cb, combobox, projectlist)
        btnOK.set_sensitive(False)
        #Set combobox to lock btnOK, so we can't press OK until we have selected a project
        combobox.connect('changed', self.lock_btnOK, combobox, btnOK)
        btnCANCEL = GtkStockButton('close','Close')
        btnCANCEL.connect('clicked', Gtk.main_quit)
        #Now fill the hbox.
        hbox.pack_start(btnCANCEL, True, True, 0)
        hbox.pack_start(btnNEW, True, True, 50)
        hbox.pack_start(btnOK, True, True, 0)
        #Now build the vbox
        vbox.pack_start(logo, False, False, 0)
        vbox.pack_start(label0, False, False, 0)
        vbox.pack_start(label, False, False, 0)
        vbox.pack_start(combobox, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)
        #And show everything.
        self.show_all()

    def lock_btnOK(self, jnk_unused, combobox, btnOK):
        ''' locks btnOK if we haven't selected a project'''
        index = combobox.get_active()
        if index:
            btnOK.set_sensitive(True)
        else:
            btnOK.set_sensitive(False)
        return
