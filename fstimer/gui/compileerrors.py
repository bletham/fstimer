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
'''Handling of the window dedicated to the display of registration's compilation's errors'''

import pygtk
pygtk.require('2.0')
import gtk
import fstimer.gui

class CompilationErrorsWin(gtk.Window):
    '''Handling of the window dedicated to the display of registration's compilation's errors'''

    def __init__(self, path, parent, errors, fields, timedict, allok_cb):
        '''Builds and display the compilation error window'''
        super(CompilationErrorsWin, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.path = path
        self.errors = errors
        self.fields = fields
        self.timedict = timedict
        self.allok_cb = allok_cb
        self.corerrorswin = None
        self.corerrorlist = None
        self.corerrortreeview = None
        self.modify_bg(gtk.STATE_NORMAL, fstimer.gui.bgcolor)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title('fsTimer - ' + path)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', lambda b, jnk: self.hide())
        self.set_border_width(10)
        self.set_size_request(450, 300)
        # make a liststore with all of the overloaded IDs (that is,
        # the keys of errors) and put it in a scrolled window
        comperrorsw = gtk.ScrolledWindow()
        comperrorsw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        comperrorsw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.errorlist = gtk.ListStore(str)
        self.errortreeview = gtk.TreeView()
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Overloaded IDs', rendererText, text=0)
        column.set_sort_column_id(0)
        self.errortreeview.append_column(column)
        # add on the IDs from errors
        for errorid in errors.keys():
            self.errorlist.append([errorid])
        self.errortreeview.set_model(self.errorlist)
        comperrorsw.add(self.errortreeview)
        errvbox1 = gtk.VBox(False, 8)
        errvbox1.pack_start(gtk.Label('These IDs were assigned to multiple entries.\nThey will be left unassigned.'), False, False, 0)
        errvbox1.pack_start(comperrorsw, True, True, 0)
        vbox1align = gtk.Alignment(0, 0, 1, 1)
        vbox1align.add(errvbox1)
        # buttons
        btnVIEW = gtk.Button('View ID entries')
        btnVIEW.connect('clicked', self.view_entries_clicked)
        btnOK = gtk.Button(stock=gtk.STOCK_OK)
        btnOK.connect('clicked', self.ok_error)
        errvbalign = gtk.Alignment(1, 0, 0, 0)
        vbox2 = gtk.VBox(False, 10)
        vbox2.pack_start(errvbalign, True, True, 0)
        vbox2.pack_start(btnVIEW, False, False, 0)
        vbox2.pack_start(btnOK, False, False, 0)
        hbox = gtk.HBox(False, 10)
        hbox.pack_start(vbox1align, False, False, 0)
        hbox.pack_start(vbox2, False, False, 0)
        self.add(hbox)
        self.show_all()

    def view_entries_clicked(self, jnk_unused):
        '''Handles click on View Id entries
           Loads a new window that will list the registration entries overloaded.
           Then gives an option to keep one of the registration entries'''
        selection = self.errortreeview.get_selection()
        treeiter = selection.get_selected()[1]
        if treeiter:
            current_id = self.errorlist.get_value(treeiter, 0)
            # Define the new window
            self.corerrorswin = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.corerrorswin.modify_bg(gtk.STATE_NORMAL, fstimer.gui.bgcolor)
            self.corerrorswin.set_transient_for(self)
            self.corerrorswin.set_modal(True)
            self.corerrorswin.set_title('fsTimer - ' + self.path)
            self.corerrorswin.set_position(gtk.WIN_POS_CENTER)
            self.corerrorswin.connect('delete_event', lambda b, jnk: self.corerrorswin.hide())
            self.corerrorswin.set_border_width(10)
            self.corerrorswin.set_size_request(800, 300)
            # This will be a liststore in a treeview in a scrolled window, as usual
            corerrorsw = gtk.ScrolledWindow()
            corerrorsw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
            corerrorsw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            self.corerrorlist = gtk.ListStore(*[str for field in self.fields])
            self.corerrortreeview = gtk.TreeView()
            # Now define each column in the treeview
            # Take these from self.fields
            for (colid, field) in enumerate(self.fields):
                column = gtk.TreeViewColumn(field, gtk.CellRendererText(), text=colid)
                column.set_sort_column_id(colid)
                self.corerrortreeview.append_column(column)
            # Add in the info from self.errors
            for reg in self.errors[current_id]:
                self.corerrorlist.append([reg[field] for field in self.fields])
            self.corerrortreeview.set_model(self.corerrorlist)
            corerrorsw.add(self.corerrortreeview)
            errvbox1 = gtk.VBox(False, 8)
            errvbox1.pack_start(gtk.Label('''These entries share the same ID.
Use "Keep entry" to associate an entry with the ID.
Otherwise, press "OK" to continue, no entry will be associated with this ID.'''), False, False, 0)
            errvbox1.pack_start(corerrorsw, True, True, 0)
            vbox1align = gtk.Alignment(0, 0, 1, 1)
            vbox1align.add(errvbox1)
            #Now build a table for the buttons
            errtable = gtk.Table(2, 1, False)
            errtable.set_row_spacings(5)
            errtable.set_col_spacings(5)
            errtable.set_border_width(5)
            btnKEEP = gtk.Button('Keep entry')
            btnKEEP.connect('clicked', self.keep_correct, current_id, treeiter)
            btnCANCEL = gtk.Button(stock=gtk.STOCK_OK)
            btnCANCEL.connect('clicked', lambda b: self.corerrorswin.hide())
            vsubbox = gtk.VBox(False, 8)
            vsubbox.pack_start(btnCANCEL, False, False, 0)
            errvspacer = gtk.Alignment(1, 1, 0, 0)
            errvspacer.add(vsubbox)
            errtable.attach(errvspacer, 0, 1, 1, 2)
            errvbox2 = gtk.VBox(False, 8)
            errvbox2.pack_start(btnKEEP, False, False, 0)
            errvbalign = gtk.Alignment(1, 0, 0, 0)
            errvbalign.add(errvbox2)
            errtable.attach(errvbalign, 0, 1, 0, 1)
            errhbox = gtk.HBox(False, 8)
            errhbox.pack_start(vbox1align, True, True, 0)
            errhbox.pack_start(errtable, False, False, 0)
            self.corerrorswin.add(errhbox)
            self.corerrorswin.show_all()

    def keep_correct(self, jnk_unused, current_id, treeiter1):
        '''Handles click on Keep entry button
           Replace timingdict with the chosen entry,
           and remove it from the error list'''
        selection = self.corerrortreeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            new_vals = {}
            for (colid, field) in enumerate(self.fields):
                new_vals[field] = model.get_value(treeiter, colid)
            # Replace the timedict entry with the selected entry
            self.timedict[current_id] = new_vals
            # Remove this ID from the errors list
            del self.errors[current_id]
            # And remove it from the error liststore
            self.errorlist.remove(treeiter1)
            # we are now done correcting this error
            self.corerrorswin.hide()
            # if there are no more errors to correct, we move on.
            if not self.errorlist.get_iter_first():
                self.hide()
                self.allok_cb(True)

    def ok_error(self, jnk_unused):
        '''Handles click on OK button
           Remove the remaining errors from the timingdict'''
        for reg in self.errors.keys():
            # these are the remaining errors
            self.timedict.pop(reg)
        self.hide()
        self.allok_cb(True)
