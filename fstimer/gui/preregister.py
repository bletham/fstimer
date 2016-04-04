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
'''Handling of the window handling preregistration setup'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import fstimer.gui
import os
from fstimer.gui.util_classes import MsgDialog
from fstimer.gui.GtkStockButton import GtkStockButton

class PreRegistrationWin(Gtk.Window):
    '''Handling of the window handling preregistration setup'''

    def __init__(self, path, set_registration_file_cb, handle_registration_cb):
        '''Builds and display the window handling preregistration
           set the computers registration ID, and optionally choose a pre-registration json'''
        super(PreRegistrationWin, self).__init__(Gtk.WindowType.TOPLEVEL)
        self.path = path
        self.set_registration_file_cb = set_registration_file_cb
        self.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        self.set_icon_from_file('fstimer/data/icon.png')
        self.set_title('fsTimer - ' + os.path.basename(path))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('delete_event', lambda b, jnk: self.hide())
        self.set_border_width(10)
        # Start with some intro text.
        prereglabel1 = Gtk.Label('Give a unique number to each computer used for registration.\nSelect a pre-registration file, if available.')
        # Continue to the spinner
        preregtable = Gtk.Table(3, 2, False)
        preregtable.set_row_spacings(5)
        preregtable.set_col_spacings(5)
        preregtable.set_border_width(10)
        regid = Gtk.Adjustment(value=1, lower=1, upper=99, step_incr=1)
        regid_btn = Gtk.SpinButton(digits=0, climb_rate=0)
        regid_btn.set_adjustment(regid)
        preregtable.attach(regid_btn, 0, 1, 0, 1)
        preregtable.attach(Gtk.Label(label="This computer's registration number"), 1, 2, 0, 1)
        preregbtnFILE = Gtk.Button('Select pre-registration')
        preregbtnFILE.connect('clicked', self.file_selected)
        preregtable.attach(preregbtnFILE, 0, 1, 2, 3)
        self.preregfilelabel = Gtk.Label(label='')
        self.preregfilelabel.set_markup('<span color="blue">No pre-registration selected.</span>')
        preregtable.attach(self.preregfilelabel, 1, 2, 2, 3)
        ## buttons
        prereghbox = Gtk.HBox(True, 0)
        preregbtnOK = GtkStockButton(Gtk.STOCK_OK,"OK")
        preregbtnOK.connect('clicked', self.preregister_ok_cb, regid_btn, handle_registration_cb)
        preregbtnCANCEL = GtkStockButton(Gtk.STOCK_CANCEL,"Cancel")
        preregbtnCANCEL.connect('clicked', lambda b: self.hide())
        prereghbox.pack_start(preregbtnOK, False, False, 5)
        prereghbox.pack_start(preregbtnCANCEL, False, False, 5)
        #Vbox
        preregvbox = Gtk.VBox(False, 0)
        preregbtnhalign = Gtk.Alignment.new(1, 0, 0, 0)
        preregbtnhalign.add(prereghbox)
        preregvbox.pack_start(prereglabel1, False, False, 5)
        preregvbox.pack_start(preregtable, False, False, 5)
        preregvbox.pack_start(preregbtnhalign, False, False, 5)
        self.add(preregvbox)
        self.show_all()

    def file_selected(self, jnk_unused):
        '''Handle selection of a pre-reg file using a filechooser.'''
        chooser = Gtk.FileChooserDialog(title='Select pre-registration file', parent=self, action=Gtk.FileChooserAction.OPEN, buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
        ffilter = Gtk.FileFilter()
        ffilter.set_name('Registration files')
        ffilter.add_pattern('*_registration_*.json')
        chooser.add_filter(ffilter)
        chooser.set_current_folder(self.path)
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = chooser.get_filename()
            try:
                self.set_registration_file_cb(filename)
                self.preregfilelabel.set_markup('<span color="blue">Pre-registration '+os.path.basename(filename)+' loaded.</span>')
            except (IOError, ValueError):
                self.preregfilelabel.set_markup('<span color="red">ERROR! Failed to load '+os.path.basename(filename)+'.</span>')
        chooser.destroy()
        return

    def preregister_ok_cb(self, jnk_unused, regid_btn, handle_registration_cb):
        '''If OK is pushed on the pre-register window.'''
        #First check if the file already exists
        regid = regid_btn.get_value_as_int()
        filename = os.path.join(self.path, os.path.basename(self.path)+'_registration_'+str(regid)+'.json')
        if os.path.exists(filename):
            #Raise a warning window
            md = MsgDialog(self, 'warning', 'OK_CANCEL', 'Proceed?', "A file with this registration number already exists.\nIf you continue it will be overwritten!")
            resp = md.run()
            md.destroy()
            #Check the result.
            if resp == Gtk.ResponseType.CANCEL:
                #Do nothing.
                return
        #Else, continue on.
        handle_registration_cb(regid)