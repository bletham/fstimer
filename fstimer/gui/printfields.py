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
'''Handling of the window dedicated to the definition of the print
   fields'''

import gi
import re
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import fstimer.gui
from fstimer.gui.GtkStockButton import GtkStockButton
from fstimer.gui.util_classes import MsgDialog

class PrintFieldsWin(Gtk.Window):
    '''Handling of the window dedicated to the definition of the field
       to reset when registering several members of a family'''

    def __init__(self, fields, printfields, back_clicked_cb, next_clicked_cb, parent, edit):
        '''Creates print fields window'''
        super(PrintFieldsWin, self).__init__(Gtk.WindowType.TOPLEVEL)
        self.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_size_request(600, 600)
        self.set_title('fsTimer - Choose results fields')
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(20)
        self.connect('delete_event', lambda b, jnk: self.hide())
        self.printfields = printfields
        self.fields = fields
        # Now create the vbox.
        vbox = Gtk.VBox(False, 2)
        self.add(vbox)
        # Now add the text.
        label1_0 = Gtk.Label("Choose the fields to show on the results printout.\nPress 'Forward' to continue with the default settings, or make edits below.\n")
        label1_1 = Gtk.Label()
        label1_1.set_markup('<b>Registration fields</b>')
        vbox.pack_start(label1_0, False, False, 0)
        vbox.pack_start(label1_1, False, False, 0)
        reg_sw = Gtk.ScrolledWindow()
        reg_sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        reg_sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        vbox_btn = Gtk.VBox(False, 2)
        btnlist = []
        for field in self.fields:
            btnlist.append(Gtk.CheckButton(field))
            if field in self.printfields:
                btnlist[-1].set_active(True)
            else:
                btnlist[-1].set_active(False)
            vbox_btn.pack_start(btnlist[-1], True, True, 0)
        reg_sw.add_with_viewport(vbox_btn)
        vbox.pack_start(reg_sw, True, True, 5)
        label1_2 = Gtk.Label()
        label1_2.set_markup('<b>Computed results</b>')
        vbox.pack_start(label1_2, False, False, 0)
        btn_time = Gtk.CheckButton('Time')
        if 'Time' in self.printfields:
            btn_time.set_active(True)
        # Pace buttons
        btn_pace = Gtk.CheckButton('Pace')
        label_pace = Gtk.Label('     Distance:')
        entry_pace = Gtk.Entry()
        entry_pace.set_max_length(5)
        entry_pace.set_width_chars(5)
        # Fill it in
        if 'Pace' in self.printfields:
            btn_pace.set_active(True)
            entry_pace.set_text(str(float(self.printfields['Pace'].split('/')[-1])))
        hbox_pace = Gtk.HBox(False, 5)
        hbox_pace.pack_start(btn_pace, False, False, 0)
        hbox_pace.pack_start(label_pace, False, False, 2)
        hbox_pace.pack_start(entry_pace, False, False, 2)
        vbox.pack_start(btn_time, False, False, 0)
        vbox.pack_start(hbox_pace, False, False, 0)
        vbox.pack_start(Gtk.Label("\nCustom expressions ({Time} is in seconds):"), False, False, 0)
        self.customview = Gtk.TreeView()
        # Make the model, a liststore with columns str, bool, str
        self.custommodel = Gtk.ListStore(str, str)
        for field in self.printfields:
            if field not in self.fields and field not in ['Time', 'Pace']:
                self.custommodel.append((field, self.printfields[field]))
        self.customview.set_model(self.custommodel)
        selection = self.customview.get_selection()
        # Add following columns to the treeview :
        # field name | expression
        name_renderer = Gtk.CellRendererText()
        name_renderer.set_property("editable", True)
        name_renderer.connect("edited", self.name_edit)
        column = Gtk.TreeViewColumn('Name', name_renderer, text=0)
        self.customview.append_column(column)
        code_renderer = Gtk.CellRendererText()
        code_renderer.set_property("editable", True)
        code_renderer.connect("edited", self.code_edit)
        column = Gtk.TreeViewColumn('Expression', code_renderer, text=1)
        self.customview.append_column(column)
        # Create scrolled window, in an alignment
        customsw = Gtk.ScrolledWindow()
        customsw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        customsw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        customsw.add(self.customview)
        customalgn = Gtk.Alignment.new(0, 0, 1, 1)
        customalgn.add(customsw)
        # Now we put the buttons on the side.
        vbox2 = Gtk.VBox(False, 10)
        btnREMOVE = GtkStockButton(Gtk.STOCK_REMOVE,"Remove")
        btnREMOVE.connect('clicked', self.custom_remove, selection)
        vbox2.pack_start(btnREMOVE, False, False, 0)
        btnNEW = GtkStockButton(Gtk.STOCK_NEW,"New")
        btnNEW.connect('clicked', self.custom_new, selection)
        vbox2.pack_start(btnNEW, False, False, 0)
        # And an hbox for the fields and the buttons
        hbox4 = Gtk.HBox(False, 0)
        hbox4.pack_start(customalgn, True, True, 10)
        hbox4.pack_start(vbox2, False, False, 0)
        vbox_comp = Gtk.VBox(False, 0)
        vbox_comp.pack_start(hbox4, True, True, 0)
        vbox.pack_start(vbox_comp, False, False, 0)
        # And an hbox with 2 buttons
        hbox = Gtk.HBox(False, 0)
        btnCANCEL = GtkStockButton(Gtk.STOCK_CANCEL,"Cancel")
        btnCANCEL.connect('clicked', lambda btn: self.hide())
        alignCANCEL = Gtk.Alignment.new(0, 0, 0, 0)
        alignCANCEL.add(btnCANCEL)
        btnBACK = GtkStockButton(Gtk.STOCK_GO_BACK,"Back")
        btnBACK.connect('clicked', back_clicked_cb, btnlist, btn_time, btn_pace, entry_pace, self.printfields)
        btnNEXT = GtkStockButton(Gtk.STOCK_GO_FORWARD,"Next")
        btnNEXT.connect('clicked', next_clicked_cb, btnlist, btn_time, btn_pace, entry_pace, self.printfields, edit)
        ##And populate
        hbox.pack_start(alignCANCEL, True, True, 0)
        hbox.pack_start(btnBACK, False, False, 2)
        hbox.pack_start(btnNEXT, False, False, 0)
        vbox.pack_start(hbox, False, False, 8)
        self.show_all()

    def custom_remove(self, jnk_unused, selection):
        '''handles a click on REMOVE button'''
        treeiter1 = selection.get_selected()[1]
        if treeiter1:
            row = self.custommodel.get_path(treeiter1)[0]
            field = self.custommodel.get_value(treeiter1, 0)
            self.custommodel.remove(treeiter1)
            self.printfields.pop(field)
            selection.select_path((row, ))
        return

    def custom_new(self, jnk_unused, selection):
        '''handles a click on NEW button'''
        # create new name
        name = 'Custom field'
        i = 1
        while name in self.printfields:
            name = 'Custom field%d' % i
            i = i + 1
        # append new line with default content
        self.printfields[name] = '{Time}'
        self.custommodel.append((name, '{Time}'))
        return

    def name_edit(self, widget, path, text):
        '''handles a change of a ranking name'''
        treeiter = self.custommodel.get_iter(path)
        old_name = self.custommodel.get_value(treeiter, 0)
        # Check if it was changed
        if text != old_name:
            if text in ['Time', 'Pace']:
                md = MsgDialog(self, 'error', 'OK', 'Error!', 'Names "Time" and "Pace" are reserved.')
                md.run()
                md.destroy()
            elif text not in self.printfields and text not in self.fields:
                self.custommodel[path][0] = text
                self.printfields[text] = self.printfields[old_name]
                self.printfields.pop(old_name)
            else:
                md = MsgDialog(self, 'error', 'OK', 'Error!', 'Field name "%s" is already used!' % text)
                md.run()
                md.destroy()
        return
    
    def code_edit(self, widget, path, text):
        '''handles a change of the ranking code'''
        # Validate the code
        try:
            # First make sure all of the variables are Time or a registration field
            vars_ = re.findall("\{[^}]+\}", text)
            for var in vars_:
                name = var[1:-1]
                if not (name in self.fields or name == 'Time'):
                    raise KeyError('Cannot find variable {}'.format(name))
            # Now check that the operations work, by plugging in a float for Time, and a string
            # for everything else.
            text_test = str(text)
            for var in vars_:
                if var == '{Time}':
                    text_test = text_test.replace(var, "3.14159")
                if var == '{Age}':
                    text_test = text_test.replace(var, "20")
                else:
                    # Use a string of a number so that int() works
                    # In the future we will have typed fields.
                    text_test = text_test.replace(var, "'1000000001'")
            eval(text_test)
        except Exception as e:
            md = MsgDialog(self, 'error', 'OK', 'Error!', 'Invalid code:\n\n{}\n\nSee documentation.'.format(e))
            md.run()
            md.destroy()
            return
        treeiter = self.custommodel.get_iter(path)
        name = self.custommodel.get_value(treeiter, 0)
        self.custommodel[path][1] = text
        self.printfields[name] = text
        return