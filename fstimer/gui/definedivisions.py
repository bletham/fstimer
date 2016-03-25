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
'''Handling of the window where divisions are defined'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import fstimer.gui
from fstimer.gui.GtkStockButton import GtkStockButton

class DivisionsWin(Gtk.Window):
    '''Handling of the window where divisions are defined'''

    def __init__(self, fields, fieldsdic, divisions, back_clicked_cb, next_clicked_cb, parent):
        '''Creates divisions window'''
        super(DivisionsWin, self).__init__(Gtk.WindowType.TOPLEVEL)
        self.divisions = divisions
        self.fields = fields
        self.fieldsdic = fieldsdic
        self.winnewdiv = None
        self.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title('fsTimer - Divisions')
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(20)
        self.set_size_request(800, 500)
        self.connect('delete_event', lambda b, jnk_unused: self.hide())
        # Now create the vbox.
        vbox = Gtk.VBox(False, 10)
        self.add(vbox)
        # Now add the text.
        label2_0 = Gtk.Label("""Specify the divisions for reporting divisional places.\
        \nPress 'Forward' to continue with the default settings, or make edits below.\
        \n\nDivisions can be any combination of age range and combobox fields.""")
        # Make the liststore, with columns:
        # name | min age | max age | (... all other combobox fields...)
        # To do this we first count the number of combobox fields
        ncbfields = len([field for field in fields if fieldsdic[field]['type'] == 'combobox'])
        self.divmodel = Gtk.ListStore(*[str for i_unused in range(ncbfields+3)])
        #We will put the liststore in a treeview
        self.divview = Gtk.TreeView()
        #Add each of the columns
        Columns = {}
        Columns[1] = Gtk.TreeViewColumn('Division name', Gtk.CellRendererText(), text=0)
        self.divview.append_column(Columns[1])
        Columns[2] = Gtk.TreeViewColumn('Min age', Gtk.CellRendererText(), text=1)
        self.divview.append_column(Columns[2])
        Columns[3] = Gtk.TreeViewColumn('Max age', Gtk.CellRendererText(), text=2)
        self.divview.append_column(Columns[3])
        #And now the additional columns
        textcount = 3
        for field in fields:
            if fieldsdic[field]['type'] == 'combobox':
                Columns[field] = Gtk.TreeViewColumn(field, Gtk.CellRendererText(), text=textcount)
                textcount += 1
                self.divview.append_column(Columns[field])
        #Now we populate the model with the default fields
        divmodelrows = {}
        for ii, div in enumerate(divisions):
            #Add in the divisional name
            divmodelrows[ii] = [div[0]]
            #Next the two age columns
            if 'Age' in  div[1]:
                divmodelrows[ii].extend([str(div[1]['Age'][0]), str(div[1]['Age'][1])])
            else:
                divmodelrows[ii].extend(['', ''])
            #And then all other columns
            for field in fields:
                if fieldsdic[field]['type'] == 'combobox':
                    if field in div[1]:
                        divmodelrows[ii].append(div[1][field])
                    else:
                        divmodelrows[ii].append('')
            #All done! Add this row in.
            self.divmodel.append(divmodelrows[ii])
        #Done there.
        self.divview.set_model(self.divmodel)
        selection = self.divview.get_selection()
        #And put it in a scrolled window, in an alignment
        divsw = Gtk.ScrolledWindow()
        divsw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        divsw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        divsw.add(self.divview)
        divalgn = Gtk.Alignment.new(0, 0, 1, 1)
        divalgn.add(divsw)
        #Now we put the buttons on the side.
        vbox2 = Gtk.VBox(False, 10)
        btnUP = GtkStockButton(Gtk.STOCK_GO_UP,'Up')
        btnUP.connect('clicked', self.div_up, selection)
        vbox2.pack_start(btnUP, False, False, 0)
        btnDOWN = GtkStockButton(Gtk.STOCK_GO_DOWN,'Down')
        btnDOWN.connect('clicked', self.div_down, selection)
        vbox2.pack_start(btnDOWN, False, False, 0)
        btnEDIT = GtkStockButton(Gtk.STOCK_EDIT,'Edit')
        btnEDIT.connect('clicked', self.div_edit, selection)
        vbox2.pack_start(btnEDIT, False, False, 0)
        btnREMOVE = GtkStockButton(Gtk.STOCK_REMOVE,'Remove')
        btnREMOVE.connect('clicked', self.div_remove, selection)
        vbox2.pack_start(btnREMOVE, False, False, 0)
        btnNEW = GtkStockButton(Gtk.STOCK_NEW,'New')
        btnNEW.connect('clicked', self.div_new, ('', {}), None)
        vbox2.pack_start(btnNEW, False, False, 0)
        #And an hbox for the fields and the buttons
        hbox4 = Gtk.HBox(False, 0)
        hbox4.pack_start(divalgn, True, True, 10)
        hbox4.pack_start(vbox2, False, False, 0)
        ##And an hbox with 3 buttons
        hbox3 = Gtk.HBox(False, 0)
        btnCANCEL = GtkStockButton(Gtk.STOCK_CANCEL,'Cancel')
        btnCANCEL.connect('clicked', lambda btn: self.hide())
        alignCANCEL = Gtk.Alignment.new(0, 0, 0, 0)
        alignCANCEL.add(btnCANCEL)
        btnBACK = GtkStockButton(Gtk.STOCK_GO_BACK,'Back')
        btnBACK.connect('clicked', back_clicked_cb)
        btnNEXT = GtkStockButton(Gtk.STOCK_GO_FORWARD,'Next')
        btnNEXT.connect('clicked', next_clicked_cb)
        ##And populate
        hbox3.pack_start(alignCANCEL, True, True, 0)
        hbox3.pack_start(btnBACK, False, False, 2)
        hbox3.pack_start(btnNEXT, False, False, 0)
        alignText = Gtk.Alignment.new(0, 0, 0, 0)
        alignText.add(label2_0)
        vbox.pack_start(alignText, False, False, 0)
        vbox.pack_start(hbox4, True, True, 0)
        vbox.pack_start(hbox3, False, False, 10)
        self.show_all()

    def div_up(self, jnk_unused, selection):
        '''handles a click on UP button'''
        model, treeiter1 = selection.get_selected()
        if treeiter1:
            row = self.divmodel.get_path(treeiter1)
            row = row[0]
            if row > 0:
                # this isn't the bottom item, so we can move it up.
                treeiter2 = model.get_iter(row-1)
                self.divmodel.swap(treeiter1, treeiter2)
                self.divisions[row], self.divisions[row-1] = self.divisions[row-1], self.divisions[row]
        return

    def div_down(self, jnk_unused, selection):
        '''handles a click on DOWN button'''
        model, treeiter1 = selection.get_selected()
        if treeiter1:
            row = self.divmodel.get_path(treeiter1)
            row = row[0]
            if row < len(self.divisions)-1:
                #this isn't the bottom item, so we can move it down.
                treeiter2 = model.get_iter(row+1)
                self.divmodel.swap(treeiter1, treeiter2)
                self.divisions[row], self.divisions[row+1] = self.divisions[row+1], self.divisions[row]
        return

    def div_edit(self, jnk_unused, selection):
        '''handles a click on EDIT button'''
        treeiter1 = selection.get_selected()[1]
        if treeiter1:
            row = self.divmodel.get_path(treeiter1)
            row = row[0]
            self.div_new(None, self.divisions[row], treeiter1)
        return

    def div_new(self, jnk_unused, divtupl, treeiter):
        '''handles a click on NEW button'''
        self.winnewdiv = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.winnewdiv.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        self.winnewdiv.set_transient_for(self)
        self.winnewdiv.set_modal(True)
        self.winnewdiv.set_title('fsTimer - New division')
        self.winnewdiv.set_position(Gtk.WindowPosition.CENTER)
        self.winnewdiv.set_border_width(20)
        self.winnewdiv.connect('delete_event', lambda b, jnk_unused: self.winnewdiv.hide())
        #Prepare for packing.
        vbox = Gtk.VBox(False, 10)
        windescr = Gtk.Label('Use the checkboxes to select which fields to use to define this division,\nand then select the corresponding value to be used for this division.')
        vbox.pack_start(windescr, False, False, 0)
        HBoxes = {}
        CheckButtons = {}
        ComboBoxes = {}
        #Process the input
        divnamein = divtupl[0]
        divdic = divtupl[1]
        #First name of the divisional.
        divnamelbl = Gtk.Label(label='Division name:')
        divnameentry = Gtk.Entry()
        divnameentry.set_max_length(80)
        divnameentry.set_width_chars(40)
        divnameentry.set_text(divnamein) #set to initial value
        HBoxes[1] = Gtk.HBox(False, 10) #an int as key so it will never collide with a user field
        HBoxes[1].pack_start(divnamelbl, False, False, 0)
        HBoxes[1].pack_start(divnameentry, False, False, 0)
        vbox.pack_start(HBoxes[1], False, False, 0)
        #Then do Age
        CheckButtons['Age'] = Gtk.CheckButton(label='Age:')
        if 'Age' in divdic:
            #if minage, then also maxage - we always have both.
            CheckButtons['Age'].set_active(True)
            minageadj = Gtk.Adjustment(value=divdic['Age'][0], lower=0, upper=120, step_incr=1)
            maxageadj = Gtk.Adjustment(value=divdic['Age'][1], lower=0, upper=120, step_incr=1)
        else:
            minageadj = Gtk.Adjustment(value=0, lower=0, upper=120, step_incr=1)
            maxageadj = Gtk.Adjustment(value=120, lower=0, upper=120, step_incr=1)
        minagelbl = Gtk.Label(label='Min age (inclusive):')
        minagebtn = Gtk.SpinButton(digits=0, climb_rate=0)
        minagebtn.set_adjustment(minageadj)
        maxagelbl = Gtk.Label(label='Max age (inclusive):')
        maxagebtn = Gtk.SpinButton(digits=0, climb_rate=0)
        maxagebtn.set_adjustment(maxageadj)
        #Make an hbox of it.
        HBoxes['Age'] = Gtk.HBox(False, 10)
        HBoxes['Age'].pack_start(CheckButtons['Age'], False, False, 0)
        HBoxes['Age'].pack_start(minagelbl, False, False, 0)
        HBoxes['Age'].pack_start(minagebtn, False, False, 0)
        HBoxes['Age'].pack_start(maxagelbl, False, False, 0)
        HBoxes['Age'].pack_start(maxagebtn, False, False, 0)
        vbox.pack_start(HBoxes['Age'], False, False, 0)
        #And now all other combobox fields
        for field in self.fields:
            if self.fieldsdic[field]['type'] == 'combobox':
                #Add it.
                CheckButtons[field] = Gtk.CheckButton(label=field+':')
                ComboBoxes[field] = Gtk.ComboBoxText()
                for option in self.fieldsdic[field]['options']:
                    ComboBoxes[field].append_text(option)
                    if field in divdic and divdic[field]:
                        CheckButtons[field].set_active(True) #the box is checked
                        ComboBoxes[field].set_active(self.fieldsdic[field]['options'].index(divdic[field])) #set to initial value
                #Put it in an HBox
                HBoxes[field] = Gtk.HBox(False, 10)
                HBoxes[field].pack_start(CheckButtons[field], False, False, 0)
                HBoxes[field].pack_start(ComboBoxes[field], False, False, 0)
                vbox.pack_start(HBoxes[field], False, False, 0)
        #On to the bottom buttons
        btnOK = GtkStockButton(Gtk.STOCK_OK,'OK')
        btnOK.connect('clicked', self.winnewdivOK, treeiter, CheckButtons, ComboBoxes, minagebtn, maxagebtn, divnameentry)
        btnCANCEL = GtkStockButton(Gtk.STOCK_CANCEL,'CANCEL')
        btnCANCEL.connect('clicked', lambda b: self.winnewdiv.hide())
        cancel_algn = Gtk.Alignment.new(0, 0, 0, 0)
        cancel_algn.add(btnCANCEL)
        hbox3 = Gtk.HBox(False, 10)
        hbox3.pack_start(cancel_algn, True, True, 0)
        hbox3.pack_start(btnOK, False, False, 0)
        vbox.pack_start(hbox3, False, False, 0)
        self.winnewdiv.add(vbox)
        self.winnewdiv.show_all()

    def div_remove(self, jnk_unused, selection):
        '''handles a click on REMOVE button'''
        treeiter1 = selection.get_selected()[1]
        if treeiter1:
            row = self.divmodel.get_path(treeiter1)
            row = row[0]
            self.divmodel.remove(treeiter1)
            self.divisions.pop(row)
            selection.select_path((row, ))

    def winnewdivOK(self, jnk_unused, treeiter, CheckButtons, ComboBoxes, minagebtn, maxagebtn, divnameentry):
        '''handles a click on OK button'''
        #First get the division name
        div = (divnameentry.get_text(), {}) #this will be the new entry in self.divisions
        #Now get age, if included.
        if CheckButtons['Age'].get_active():
            minage = minagebtn.get_value_as_int()
            maxage = maxagebtn.get_value_as_int()
            div[1]['Age'] = (minage, maxage)
        #And now go through the other fields.
        for field, btn in CheckButtons.items():
            if field != 'Age' and btn.get_active() and ComboBoxes[field].get_active() > -1:
                div[1][field] = self.fieldsdic[field]['options'][ComboBoxes[field].get_active()]
        if treeiter:
            #we are replacing a division
            row = self.divmodel.get_path(treeiter)
            row = row[0]
            self.divisions[row] = div #replace the old division with the new one in self.divisions
            #And now update the divmodel
            self.divmodel.set_value(treeiter, 0, div[0])
            if 'Age' in div[1]:
                self.divmodel.set_value(treeiter, 1, str(div[1]['Age'][0]))
                self.divmodel.set_value(treeiter, 2, str(div[1]['Age'][1]))
            else:
                self.divmodel.set_value(treeiter, 1, '')
                self.divmodel.set_value(treeiter, 2, '')
            colcount = 3
            for field in self.fields:
                if self.fieldsdic[field]['type'] == 'combobox':
                    if field in div[1]:
                        self.divmodel.set_value(treeiter, colcount, div[1][field])
                    else:
                        self.divmodel.set_value(treeiter, colcount, '')
                    colcount += 1
        else:
            #no treeiter- this was a new entry.
            #Add it to self.divisions
            self.divisions.append(div)
            #Add in the divisional name
            divmodelrow = [div[0]]
            #Next the two age columns
            if 'Age' in    div[1]:
                divmodelrow.extend([str(div[1]['Age'][0]), str(div[1]['Age'][1])])
            else:
                divmodelrow.extend(['', ''])
            #And then all other columns
            for field in self.fields:
                if self.fieldsdic[field]['type'] == 'combobox':
                    if field in div[1]:
                        divmodelrow.append(div[1][field])
                    else:
                        divmodelrow.append('')
            #All done! Add this row in.
            self.divmodel.append(divmodelrow)
        self.winnewdiv.hide()
