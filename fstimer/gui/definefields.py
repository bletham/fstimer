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
'''Handling of the window dedicated to the definition of the fields
   used in a project'''

import pygtk
pygtk.require('2.0')
import gtk
import fstimer.gui

class DefineFieldsWin(gtk.Window):
    '''Handles the definition of the fields in a project'''

    def __init__(self, fields, fieldsdic, back_clicked_cb, next_clicked_cb, parent):
        '''Creates fields definition window'''
        super(DefineFieldsWin, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.fields = fields
        self.fieldsdic = fieldsdic
        self.modify_bg(gtk.STATE_NORMAL, fstimer.gui.bgcolor)
        self.winnewcombo = None
        self.winnewentry = None
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title('fsTimer - New project')
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_border_width(20)
        self.set_size_request(600, 400)
        self.connect('delete_event', lambda b, jnk_unused: self.hide())
        ##Now create the vbox.
        vbox1 = gtk.VBox(False, 10)
        self.add(vbox1)
        ##Now add the text.
        label2_0 = gtk.Label("Specify the information to be collected during registration.\nPress 'Forward' to continue with the default settings, or make edits below.")
        #label2_1 = gtk.Label('Information can be collected using an entrybox or using a combobox.\n ')
        #label2_2 = gtk.Label('This is an example of an entrybox:')
        #entry_demo = gtk.Entry(max=10)
        #hbox1 = gtk.HBox(False, 0)
        #hbox1.pack_start(label2_2, False, False, 0)
        #hbox1.pack_start(entry_demo, False, False, 0)
        #label2_3 = gtk.Label('This is an example of a combobox:')
        #combo_demo = gtk.combo_box_new_text()
        #for opt in ['', 'option1', 'option2', 'option3']:
        #  combo_demo.append_text(opt)
        #hbox2 = gtk.HBox(False, 0)
        #hbox2.pack_start(label2_3, False, False, 0)
        #hbox2.pack_start(combo_demo, False, False, 0)
        #Now we put in a liststore with the settings. We start with the default settings.
        #Make the liststore, with 3 columns (title, type, settings)
        self.regfieldsmodel = gtk.ListStore(str, str, str)
        #We will put the liststore in a treeview
        self.regfieldview = gtk.TreeView()
        column = gtk.TreeViewColumn('Field', gtk.CellRendererText(), text=0)
        self.regfieldview.append_column(column)
        column = gtk.TreeViewColumn('Type', gtk.CellRendererText(), text=1)
        self.regfieldview.append_column(column)
        column = gtk.TreeViewColumn('Settings', gtk.CellRendererText(), text=2)
        self.regfieldview.append_column(column)
        #Now we populate the model with the default fields
        for field in fields:
            if fieldsdic[field]['type'] == 'entrybox':
                self.regfieldsmodel.append([field, 'entrybox', 'max characters: '+str(fieldsdic[field]['max'])])
            elif fieldsdic[field]['type'] == 'combobox':
                optstr = ''
                for opt in fieldsdic[field]['options']:
                    optstr += opt + ', '
                optstr = optstr[:-2] #drop the last ', '
                self.regfieldsmodel.append([field, 'combobox', 'options: '+optstr])
        self.regfieldview.set_model(self.regfieldsmodel)
        selection = self.regfieldview.get_selection()
        #And put it in a scrolled window, in an alignment
        regfieldsw = gtk.ScrolledWindow()
        regfieldsw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        regfieldsw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        regfieldsw.add(self.regfieldview)
        regfieldalgn = gtk.Alignment(0, 0, 1, 1)
        regfieldalgn.add(regfieldsw)
        #Now we put the buttons on the side.
        vbox2 = gtk.VBox(False, 10)
        btnUP = gtk.Button(stock=gtk.STOCK_GO_UP)
        btnUP.connect('clicked', self.regfield_up, selection)
        vbox2.pack_start(btnUP, False, False, 0)
        btnDOWN = gtk.Button(stock=gtk.STOCK_GO_DOWN)
        btnDOWN.connect('clicked', self.regfield_down, selection)
        vbox2.pack_start(btnDOWN, False, False, 0)
        btnEDIT = gtk.Button(stock=gtk.STOCK_EDIT)
        btnEDIT.connect('clicked', self.regfield_edit, selection)
        vbox2.pack_start(btnEDIT, False, False, 0)
        btnREMOVE = gtk.Button(stock=gtk.STOCK_REMOVE)
        btnREMOVE.connect('clicked', self.regfield_remove, selection)
        vbox2.pack_start(btnREMOVE, False, False, 0)
        btnNEWentry = gtk.Button('New entrybox')
        btnNEWentry.connect('clicked', self.regfield_new_entrybox, '', 0, None)
        vbox2.pack_start(btnNEWentry, False, False, 0)
        btnNEWcombo = gtk.Button('New combobox')
        btnNEWcombo.connect('clicked', self.regfield_new_combobox, '', '', None)
        vbox2.pack_start(btnNEWcombo, False, False, 0)
        selection.connect('changed', self.regfield_lock_required_fields, btnREMOVE, btnEDIT)
        #And an hbox for the fields and the buttons
        hbox4 = gtk.HBox(False, 0)
        hbox4.pack_start(regfieldalgn, True, True, 10)
        hbox4.pack_start(vbox2, False, False, 0)
        ##And an hbox with 3 buttons
        hbox3 = gtk.HBox(False, 0)
        btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
        btnCANCEL.connect('clicked', lambda btn: self.hide())
        alignCANCEL = gtk.Alignment(0, 0, 0, 0)
        alignCANCEL.add(btnCANCEL)
        btnBACK = gtk.Button(stock=gtk.STOCK_GO_BACK)
        btnBACK.connect('clicked', back_clicked_cb)
        btnNEXT = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        btnNEXT.connect('clicked', next_clicked_cb)
        ##And populate
        hbox3.pack_start(alignCANCEL, True, True, 0)
        hbox3.pack_start(btnBACK, False, False, 2)
        hbox3.pack_start(btnNEXT, False, False, 0)
        vbox1.pack_start(label2_0, False, False, 0)
        #vbox1.pack_start(label2_1, False, False, 0)
        #vbox1.pack_start(hbox1, False, False, 0)
        #vbox1.pack_start(hbox2, False, False, 0)
        vbox1.pack_start(hbox4, True, True, 0)
        vbox1.pack_start(hbox3, False, False, 10)
        self.show_all()

    def regfield_up(self, jnk_unused, selection):
        '''Handled click on the UP button'''
        model, treeiter1 = selection.get_selected()
        if treeiter1:
            row = self.regfieldsmodel.get_path(treeiter1)
            row = row[0]
            if row > 0:
                #this isn't the bottom item, so we can move it up.
                treeiter2 = model.get_iter(row-1)
                self.regfieldsmodel.swap(treeiter1, treeiter2)
                self.fields[row], self.fields[row-1] = self.fields[row-1], self.fields[row]
        return

    def regfield_down(self, jnk_unused, selection):
        '''Handled click on the DOWN button'''
        model, treeiter1 = selection.get_selected()
        if treeiter1:
            row = self.regfieldsmodel.get_path(treeiter1)
            row = row[0]
            if row < len(self.fields)-1:
                #this isn't the bottom item, so we can move it down.
                treeiter2 = model.get_iter(row+1)
                self.regfieldsmodel.swap(treeiter1, treeiter2)
                self.fields[row], self.fields[row+1] = self.fields[row+1], self.fields[row]
        return

    def regfield_edit(self, jnk_unused, selection):
        '''Handled click on the EDIT button'''
        model, treeiter1 = selection.get_selected()
        if treeiter1:
            name = model.get_value(treeiter1, 0)
            typ = model.get_value(treeiter1, 1)
            if typ == 'combobox':
                options = model.get_value(treeiter1, 2)[9:]
                self.regfield_new_combobox(None, name, options, treeiter1)
            elif typ == 'entrybox':
                maxchar = model.get_value(treeiter1, 2)[16:]
                self.regfield_new_entrybox(None, name, maxchar, treeiter1)
        return

    def regfield_new_entrybox(self, jnk_unused, name, maxchar, treeiter):
        '''Handled click on the New entrybox button'''
        self.winnewentry = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.winnewentry.modify_bg(gtk.STATE_NORMAL, fstimer.gui.bgcolor)
        self.winnewentry.set_transient_for(self)
        self.winnewentry.set_modal(True)
        self.winnewentry.set_title('fsTimer - New project')
        self.winnewentry.set_position(gtk.WIN_POS_CENTER)
        self.winnewentry.set_border_width(20)
        self.winnewentry.connect('delete_event', lambda b, jnk_unused: self.winnewentry.hide())
        label1 = gtk.Label('Field name:')
        nameentry = gtk.Entry(max=50)
        nameentry.set_text(name)
        hbox1 = gtk.HBox(False, 10)
        hbox1.pack_start(label1, False, False, 0)
        hbox1.pack_start(nameentry, False, False, 0)
        label2 = gtk.Label('Max characters:')
        maxcharadj = gtk.Adjustment(value=1, lower=1, upper=120, step_incr=1)
        maxcharbtn = gtk.SpinButton(maxcharadj, digits=0, climb_rate=0)
        maxcharbtn.set_value(int(maxchar))
        hbox2 = gtk.HBox(False, 10)
        hbox2.pack_start(label2, False, False, 0)
        hbox2.pack_start(maxcharbtn, False, False, 0)
        label3 = gtk.Label('')
        btnOK = gtk.Button(stock=gtk.STOCK_OK)
        btnOK.connect('clicked', self.winnewentryOK, treeiter, nameentry, maxcharbtn, label3)
        btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
        btnCANCEL.connect('clicked', lambda b: self.winnewentry.hide())
        cancel_algn = gtk.Alignment(0, 0, 0, 0)
        cancel_algn.add(btnCANCEL)
        hbox3 = gtk.HBox(False, 10)
        hbox3.pack_start(cancel_algn, True, True, 0)
        hbox3.pack_start(btnOK, False, False, 0)
        vbox = gtk.VBox(False, 10)
        vbox.pack_start(hbox1, False, False, 0)
        vbox.pack_start(hbox2, False, False, 0)
        vbox.pack_start(label3, False, False, 0)
        vbox.pack_start(hbox3, False, False, 0)
        self.winnewentry.add(vbox)
        self.winnewentry.show_all()
        return

    def regfield_lock_required_fields(self, selection, btnREMOVE, btnEDIT):
        '''Locks REMOVE and EDIT button for required fields'''
        model, treeiter1 = selection.get_selected()
        if treeiter1:
            name = model.get_value(treeiter1, 0)
            if name in ['Last name', 'First name', 'ID', 'Age', 'Gender']:
                #these are the hard-coded required fields
                btnREMOVE.set_sensitive(False)
                btnEDIT.set_sensitive(False)
            else:
                btnREMOVE.set_sensitive(True)
                btnEDIT.set_sensitive(True)
        return

    def regfield_new_combobox(self, jnk_unused, name, options, treeiter):
        '''Handled click on the New combobox button'''
        self.winnewcombo = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.winnewcombo.modify_bg(gtk.STATE_NORMAL, fstimer.gui.bgcolor)
        self.winnewcombo.set_transient_for(self)
        self.winnewcombo.set_modal(True)
        self.winnewcombo.set_title('fsTimer - New project')
        self.winnewcombo.set_position(gtk.WIN_POS_CENTER)
        self.winnewcombo.set_border_width(20)
        self.winnewcombo.connect('delete_event', lambda b, jnk_unused: self.winnewcombo.hide())
        label1 = gtk.Label('Field name:')
        nameentry = gtk.Entry(max=50)
        nameentry.set_text(name)
        hbox1 = gtk.HBox(False, 10)
        hbox1.pack_start(label1, False, False, 0)
        hbox1.pack_start(nameentry, False, False, 0)
        label2 = gtk.Label('Options,  separated by commas:')
        optionentry = gtk.Entry(max=50)
        optionentry.set_text(options)
        hbox2 = gtk.HBox(False, 10)
        hbox2.pack_start(label2, False, False, 0)
        hbox2.pack_start(optionentry, False, False, 0)
        label3 = gtk.Label('')
        btnOK = gtk.Button(stock=gtk.STOCK_OK)
        btnOK.connect('clicked', self.winnewcomboOK, treeiter, nameentry, optionentry, label3)
        btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
        btnCANCEL.connect('clicked', lambda b: self.winnewcombo.hide())
        cancel_algn = gtk.Alignment(0, 0, 0, 0)
        cancel_algn.add(btnCANCEL)
        hbox3 = gtk.HBox(False, 10)
        hbox3.pack_start(cancel_algn, True, True, 0)
        hbox3.pack_start(btnOK, False, False, 0)
        vbox = gtk.VBox(False, 10)
        vbox.pack_start(hbox1, False, False, 0)
        vbox.pack_start(hbox2, False, False, 0)
        vbox.pack_start(label3, False, False, 0)
        vbox.pack_start(hbox3, False, False, 0)
        self.winnewcombo.add(vbox)
        self.winnewcombo.show_all()
        return

    def regfield_remove(self, jnk_unused, selection):
        '''Handled click on the REMOVE button'''
        model_unused, treeiter1 = selection.get_selected()
        if treeiter1:
            row = self.regfieldsmodel.get_path(treeiter1)
            row = row[0]
            oldname = self.regfieldsmodel.get_value(treeiter1, 0)
            self.regfieldsmodel.remove(treeiter1)
            self.fields.pop(row)
            self.fieldsdic.pop(oldname)
        return

    def winnewcomboOK(self, jnk_unused, treeiter, nameentry1, optionentry1, label3):
        '''Handled click on the OK button of the new combo dialog'''
        optionentry = optionentry1.get_text()
        nameentry = nameentry1.get_text()
        optionlist = [a.strip() for a in optionentry.split(',')]
        optstr = ''
        for opt in optionlist:
            optstr += opt + ', '
        optstr = optstr[:-2] #drop the last ', '
        if treeiter:
            oldname = self.regfieldsmodel.get_value(treeiter, 0)
            if nameentry == oldname:
                #The original name. we only edited options. Get the new options
                self.fieldsdic[nameentry]['options'] = optionlist
                self.regfieldsmodel.set_value(treeiter, 2, 'options: '+optstr)
                self.winnewcombo.hide()
            elif nameentry in self.fields:
                #Not the original name, but an existing name.
                label3.set_markup('<span color="red">This field already exists! Try again.</span>')
            else:
                #A completely new name.
                self.fields[self.fields.index(oldname)] = nameentry #replace the name in self.fields
                self.fieldsdic.pop(oldname) #delete the old entry
                self.fieldsdic[nameentry] = {'type':'combobox', 'options':optionlist} #new entry
                self.regfieldsmodel.set_value(treeiter, 0, nameentry) #and update the liststore
                self.regfieldsmodel.set_value(treeiter, 2, 'options: '+optstr)
                self.winnewcombo.hide()
        else:
            #no treeiter- this was a new entry. Two possibilities...
            if nameentry in self.fields:
                label3.set_markup('<span color="red">This field already exists! Try again.</span>')
            else:
                self.fields.append(nameentry)
                self.fieldsdic[nameentry] = {'type':'combobox', 'options':optionlist} #new entry
                self.regfieldsmodel.append([nameentry, 'combobox', 'options: '+optstr])
                self.winnewcombo.hide()
        return

    def winnewentryOK(self, jnk_unused, treeiter, nameentry1, maxchar1, label3):
        '''Handled click on the OK button of the new entry dialog'''
        maxchar = str(maxchar1.get_value_as_int())
        nameentry = nameentry1.get_text()
        if treeiter:
            oldname = self.regfieldsmodel.get_value(treeiter, 0)
            if nameentry == oldname:
                #The original name. we only edited maxchar. Get the new maxchar
                self.fieldsdic[nameentry]['max'] = int(maxchar)
                self.regfieldsmodel.set_value(treeiter, 2, 'max characters: '+maxchar)
                self.winnewentry.hide()
            elif nameentry in self.fields:
                #Not the original name, but an existing name.
                label3.set_markup('<span color="red">This field already exists! Try again.</span>')
            else:
                #A completely new name.
                self.fields[self.fields.index(oldname)] = nameentry #replace the name in self.fields
                self.fieldsdic.pop(oldname) #delete the old entry
                self.fieldsdic[nameentry] = {'type':'entrybox', 'max':int(maxchar)} #new entry
                self.regfieldsmodel.set_value(treeiter, 0, nameentry) #and update the liststore
                self.regfieldsmodel.set_value(treeiter, 2, 'max characters: '+maxchar)
                self.winnewentry.hide()
        else:
            #no treeiter- this was a new entry. Two possibilities...
            if nameentry in self.fields:
                label3.set_markup('<span color="red">This field already exists! Try again.</span>')
            else:
                self.fields.append(nameentry)
                self.fieldsdic[nameentry] = {'type':'entrybox', 'max':int(maxchar)} #new entry
                self.regfieldsmodel.append([nameentry, 'entrybox', 'max characters: '+maxchar])
                self.winnewentry.hide()
        return

