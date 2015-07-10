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
'''Handling of the window dedicated to compilation of registrations from multiple computers'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import fstimer.gui
import os
from fstimer.gui.GtkStockButton import GtkStockButton

class CompilationWin(Gtk.Window):
    '''Handling of the window dedicated to compilation of registrations from multiple computers'''

    def __init__(self, path, merge_cb):
        '''Builds and display the compilation window'''
        super(CompilationWin, self).__init__(Gtk.WindowType.TOPLEVEL)
        self.path = path
        self.merge_cb = merge_cb
        self.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        self.set_icon_from_file('fstimer/data/icon.png')
        self.set_title('fsTimer - ' + os.path.basename(path))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('delete_event', lambda b, jnk: self.hide())
        self.set_border_width(10)
        self.set_size_request(600, 450)
        # We will use a liststore to hold the filenames of the
        # registrations to be merged, and put the liststore in a scrolledwindow
        compregsw = Gtk.ScrolledWindow()
        compregsw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        compregsw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.reglist = Gtk.ListStore(str)
        self.comptreeview = Gtk.TreeView()
        rendererText = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Registration files', rendererText, text=0)
        column.set_sort_column_id(0)
        self.comptreeview.append_column(column)
        self.comptreeview.set_model(self.reglist)
        compregsw.add(self.comptreeview)
        # We have text below the window to explain what is happening during merging
        self.comblabel = []
        for i in range(3):
            label = Gtk.Label(label='')
            label.set_alignment(0, 0.5)
            self.comblabel.append(label)
        # Pack it all
        regvbox1 = Gtk.VBox(False, 8)
        regvbox1.pack_start(Gtk.Label('Select all of the registration files to merge', True, True, 0), False, False, 0)
        regvbox1.pack_start(compregsw, True, True, 0)
        for i in range(3):
            regvbox1.pack_start(self.comblabel[i], False, False, 0)
        vbox1align = Gtk.Alignment.new(0, 0, 1, 1)
        vbox1align.add(regvbox1)
        # The buttons in a table
        regtable = Gtk.Table(2, 1, False)
        regtable.set_row_spacings(5)
        regtable.set_col_spacings(5)
        regtable.set_border_width(5)
        btnREMOVE = GtkStockButton(Gtk.STOCK_REMOVE,'Remove')
        btnREMOVE.connect('clicked', self.rm_clicked)
        btnADD = GtkStockButton(Gtk.STOCK_ADD,'Add')
        btnADD.connect('clicked', self.add_clicked)
        btnMERGE = Gtk.Button('Merge')
        btnMERGE.connect('clicked', self.merge_clicked)
        btnOK = Gtk.Button('Done')
        btnOK.connect('clicked', lambda jnk: self.hide())
        vsubbox = Gtk.VBox(False, 8)
        vsubbox.pack_start(btnMERGE, False, False, 0)
        vsubbox.pack_start(btnOK, False, False, 0)
        regvspacer = Gtk.Alignment.new(1, 1, 0, 0)
        regvspacer.add(vsubbox)
        regtable.attach(regvspacer, 0, 1, 1, 2)
        regvbox2 = Gtk.VBox(False, 8)
        regvbox2.pack_start(btnREMOVE, False, False, 0)
        regvbox2.pack_start(btnADD, False, False, 0)
        regvbalign = Gtk.Alignment.new(1, 0, 0, 0)
        regvbalign.add(regvbox2)
        regtable.attach(regvbalign, 0, 1, 0, 1)
        reghbox = Gtk.HBox(False, 8)
        reghbox.pack_start(vbox1align, True, True, 0)
        reghbox.pack_start(regtable, False, False, 0)
        #Add and show
        self.add(reghbox)
        self.show_all()

    def rm_clicked(self, jnk_unused):
        '''Handling click on Remove button'''
        selection = self.comptreeview.get_selection()
        model, comptreeiter = selection.get_selected()
        #if something was selected...
        if comptreeiter:
            model.remove(comptreeiter)

    def add_clicked(self, jnk_unused):
        '''Handling click on Add button, using a FileChooser'''
        chooser = Gtk.FileChooserDialog(title='Select registration files', action=Gtk.FileChooserAction.OPEN, buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_ADD, Gtk.ResponseType.OK))
        chooser.set_select_multiple(True)
        ffilter = Gtk.FileFilter()
        ffilter.set_name('Registration files')
        ffilter.add_pattern('*registration_*.json')
        chooser.add_filter(ffilter)
        chooser.set_current_folder(self.path)
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            filenames = chooser.get_filenames()
            for filenm in filenames:
                self.reglist.append([filenm])
        chooser.destroy()

    def merge_clicked(self, jnk_unused):
        '''Handling click on Merge button'''
        # Grab all of the filenames from the liststore
        filenames = []
        self.reglist.foreach(lambda model, gtkpath, titer: filenames.append(model.get_value(titer, 0)))
        self.merge_cb(filenames)

    def resetLabels(self):
        '''Empties text in labels'''
        for i in range(3):
            self.comblabel[i].set_markup('')

    def setLabel(self, index, txt):
        '''Set the text in one of the labels'''
        if index < 0 or index > 3:
            return
        self.comblabel[index].set_markup(txt)
