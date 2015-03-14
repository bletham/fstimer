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
'''Handling of the window dedicated to importation of pre-registration'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import fstimer.gui
import os, csv, json
import datetime

class ComboValueError(Exception):
    '''Exception launched when decoding reveals an invalid value for a combo field'''
    pass

class ImportPreRegWin(Gtk.Window):
    '''Handling of the window dedicated to importation of pre-registration'''

    def __init__(self, cwd, path, fields, fieldsdic):
        '''Builds and display the importation window'''
        super(ImportPreRegWin, self).__init__(Gtk.WindowType.TOPLEVEL)
        self.path = path
        self.cwd = cwd
        self.fields = fields
        self.fieldsdic = fieldsdic
        self.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        self.set_icon_from_file('fstimer/data/icon.png')
        self.set_title('fsTimer - ' + path)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('delete_event', lambda b, jnk: self.hide())
        self.set_border_width(10)
        self.set_size_request(600, 400)
        # Start with some intro text.
        label1 = Gtk.Label(label='Select a pre-registration csv file to import.')
        #Continue to the load file.
        btnFILE = Gtk.Button(stock=Gtk.STOCK_OPEN)
        ## Textbuffer
        textbuffer = Gtk.TextBuffer()
        try:
            textbuffer.create_tag("blue", foreground="blue")
            textbuffer.create_tag("red", foreground="red")
        except TypeError:
            pass
        textview = Gtk.TextView()
        textview.set_buffer(textbuffer)
        textview.set_editable(False)
        textview.set_cursor_visible(False)
        textsw = Gtk.ScrolledWindow()
        textsw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        textsw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        textsw.add(textview)
        textalgn = Gtk.Alignment.new(0, 0, 1, 1)
        textalgn.add(textsw)
        hbox2 = Gtk.HBox(False, 5)
        btnFILE.connect('clicked', self.select_preregistration, textbuffer)
        btn_algn = Gtk.Alignment.new(1, 0, 1, 0)
        hbox2.pack_start(btnFILE, False, False, 0)
        hbox2.pack_start(btn_algn, True, True, 0)
        ## buttons
        btnOK = Gtk.Button(stock=Gtk.STOCK_OK)
        btnOK.connect('clicked', lambda b: self.hide())
        cancel_algn = Gtk.Alignment.new(0, 0, 1, 0)
        hbox3 = Gtk.HBox(False, 10)
        hbox3.pack_start(cancel_algn, True, True, 0)
        hbox3.pack_start(btnOK, False, False, 0)
        vbox = Gtk.VBox(False, 0)
        vbox.pack_start(label1, False, False, 5)
        vbox.pack_start(hbox2, False, True, 5)
        vbox.pack_start(textalgn, True, True, 5)
        vbox.pack_start(hbox3, False, False, 0)
        self.add(vbox)
        self.show_all()

    def propose_advanced_import(self, csv_fields, textbuffer1):
        '''Propose advanced import mechanism where project fields can be build
           from the csv ones using python expressions'''
        self.advancedwin = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.advancedwin.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        self.advancedwin.set_transient_for(self)
        self.advancedwin.set_modal(True)
        self.advancedwin.set_title('fsTimer - CSV import')
        self.advancedwin.set_position(Gtk.WindowPosition.CENTER)
        self.advancedwin.set_border_width(20)
        self.advancedwin.set_size_request(600, 400)
        self.advancedwin.connect('delete_event', lambda b, jnk_unused: self.advancedwin.hide())
        # top label
        toplabel = Gtk.Label("For each field, specify the corresponding CSV column.\n")
        # Treeview with 3 columns : field, combobox and free text
        self.fieldview = Gtk.TreeView()
        self.fieldview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        # Associated model with 5 columns : the 4th one is a boolean indicating
        # whether the 3rd one (Advanced mapping) should be sensitive
        self.fieldsmodel = Gtk.ListStore(str, str, str, bool)
        for field in self.fields:
            self.fieldsmodel.append([field, field if field in csv_fields else '-- select --', '', False])
        self.fieldview.set_model(self.fieldsmodel)
        # build first column (project field)
        column = Gtk.TreeViewColumn('Field', Gtk.CellRendererText(), text=0)
        self.fieldview.append_column(column)
        # vuild 2nd column (csv field to be used, as a combo box)
        combo_renderer = Gtk.CellRendererCombo()
        liststore_csv_fields = Gtk.ListStore(str)
        liststore_csv_fields.append(['-- Leave empty --'])
        for field in csv_fields:
            liststore_csv_fields.append([field])
        liststore_csv_fields.append(['-- Advanced expression --'])
        combo_renderer.set_property("model", liststore_csv_fields)
        combo_renderer.set_property("text-column", 0)
        combo_renderer.set_property("editable", True)
        combo_renderer.set_property("has-entry", False)
        column = Gtk.TreeViewColumn('CSV column', combo_renderer, text=1)
        self.fieldview.append_column(column)
        # build the 3rd column (Advanced mapping)
        advanced_renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Advanced mapping', advanced_renderer, text=2, sensitive=3, editable=3)
        self.fieldview.append_column(column)
        # handler for the combo changes
        combo_renderer.connect("edited", self.combo_changed)
        advanced_renderer.connect("edited", self.text_changed)
        # And put it in a scrolled window, in an alignment
        fieldsw = Gtk.ScrolledWindow()
        fieldsw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        fieldsw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        fieldsw.add(self.fieldview)
        fieldalgn = Gtk.Alignment.new(0, 0, 1, 1)
        fieldalgn.add(fieldsw)
        # a text buffer for errors
        textbuffer2 = Gtk.TextBuffer()
        try:
            textbuffer2.create_tag("red", foreground="red")
            textbuffer2.create_tag("blue", foreground="blue")
        except TypeError:
            pass
        textview = Gtk.TextView()
        textview.set_buffer(textbuffer2)
        textview.set_editable(False)
        textview.set_cursor_visible(False)
        # hbox for the buttons
        hbox = Gtk.HBox(False, 0)
        btnCANCEL = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        btnCANCEL.connect('clicked', self.advanced_import_cancel, textbuffer1)
        btnOK = Gtk.Button(stock=Gtk.STOCK_OK)
        btnOK.connect('clicked', self.advanced_import_ok, textbuffer1, textbuffer2)
        alignOK = Gtk.Alignment.new(1, 0, 0, 0)
        alignOK.add(btnOK)
        hbox.pack_start(btnCANCEL, False, True, 0)
        hbox.pack_start(alignOK, True, True, 0)
        # populate
        vbox = Gtk.VBox(False, 10)
        vbox.pack_start(toplabel, False, False, 0)
        vbox.pack_start(fieldalgn, True, True, 0)
        vbox.pack_start(textview, False, False, 0)
        vbox.pack_start(hbox, False, False, 10)
        self.advancedwin.add(vbox)
        self.advancedwin.show_all()

    def advanced_import_cancel(self, widget_unused, textbuffer):
        '''If cancel is pressed in the advanced import window'''
        self.advancedwin.hide()
        iter_end = textbuffer.get_end_iter()
        textbuffer.insert_with_tags_by_name(iter_end, 'Nothing done.', 'blue')

    def combo_changed(self, widget_unused, path, text):
        '''Handles a change in the combo boxes' selections'''
        self.fieldsmodel[path][1] = text
        if text == '-- Advanced expression --':
            if len(self.fieldsmodel[path][2]) == 0:
                self.fieldsmodel[path][2] = '-- enter python expression --'
            self.fieldsmodel[path][3] = True
        else:
            self.fieldsmodel[path][3] = False

    def text_changed(self, widget_unused, path, text):
        '''Handles a change in the advanced boxes'''
        self.fieldsmodel[path][2] = text

    def advanced_import_ok(self, jnk_unused, textbuffer1, textbuffer2):
        '''Handles click on OK button in the advanced interface'''
        textbuffer2.delete(textbuffer2.get_start_iter(), textbuffer2.get_end_iter())
        self.fields_mapping = {}
        for path in range(len(self.fieldsmodel)):
            field = self.fieldsmodel[path][0]
            csv_col = self.fieldsmodel[path][1]
            if csv_col == '-- select --':
                textbuffer2.insert_with_tags_by_name(textbuffer2.get_end_iter(), 'Nothing selected for field %s' % field, 'red')
                return
            elif csv_col == '-- Leave empty --' or csv_col == None:
                self.fields_mapping[field] = lambda reg, col=csv_col: ''
            elif csv_col == '-- Advanced expression --':
                try:
                    code = compile(self.fieldsmodel[path][2], '', 'eval')
                    self.fields_mapping[field] = lambda reg, code=code: eval(code)
                except SyntaxError as e:
                    iter_end = textbuffer2.get_end_iter()
                    textbuffer2.insert_with_tags_by_name(iter_end, 'Invalid syntax for expression of field %s: ' % field, 'red')
                    textbuffer2.insert_with_tags_by_name(textbuffer2.get_end_iter(), str(e), 'blue')
                    return
            else:
                self.fields_mapping[field] = lambda reg, col=csv_col: reg[col]
        self.advancedwin.hide()
        self.import_data(textbuffer1)

    def build_fields_mapping(self, csv_fields, textbuffer):
        '''Maps cvs fields to project fields and creates a dictionnary
           of lambdas to apply to a csv entry to extract each field.
           Some entries may contain strings instead of lambdas, meaning
           that the project column's value is equal to that csv column's value'''
        iter_end = textbuffer.get_end_iter()
        fields_use = [field for field in csv_fields if field in self.fields]
        textbuffer.insert_with_tags_by_name(iter_end, 'Matched csv fields: ', 'blue')
        textbuffer.insert(iter_end, ', '.join(fields_use) + '\n')
        fields_ignore = [field for field in csv_fields if field not in self.fields]
        textbuffer.insert_with_tags_by_name(iter_end, 'Did not match csv fields: ', 'red')
        textbuffer.insert(iter_end, ', '.join(fields_ignore) + '\n')
        fields_notuse = [field for field in self.fields if field not in csv_fields]
        textbuffer.insert_with_tags_by_name(iter_end, 'Did not find in csv: ', 'red')
        textbuffer.insert(iter_end, ', '.join(fields_notuse) + '\n')
        self.propose_advanced_import(csv_fields, textbuffer)

    def select_preregistration(self, jnk_unused, textbuffer):
        '''Handle selection of a pre-reg file using a filechooser'''
        chooser = Gtk.FileChooserDialog(title='Select pre-registration csv', action=Gtk.FileChooserAction.OPEN, buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
        ffilter = Gtk.FileFilter()
        ffilter.set_name('csv files')
        ffilter.add_pattern('*.csv')
        chooser.add_filter(ffilter)
        chooser.set_current_folder(os.path.join(self.cwd, self.path, ''))
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = chooser.get_filename()
            textbuffer.delete(textbuffer.get_start_iter(), textbuffer.get_end_iter())
            textbuffer.set_text('Loading '+os.path.basename(filename)+'...\n')
            try:
                fin = csv.DictReader(open(filename, 'r'))
                self.csvreg = []
                for row in fin:
                    self.csvreg.append(row)
                csv_fields = self.csvreg[0].keys()
                iter_end = textbuffer.get_end_iter()
                textbuffer.insert_with_tags_by_name(iter_end, 'Found csv fields: ', 'blue')
                textbuffer.insert(iter_end, ', '.join(csv_fields) + '\n')
                self.build_fields_mapping(csv_fields, textbuffer)
            except (IOError, IndexError, csv.Error):
                iter_end = textbuffer.get_end_iter()
                textbuffer.insert_with_tags_by_name(iter_end, 'Error! Could not open file, or no data found in file. Nothing was imported, try again.', 'red')
        chooser.destroy()

    def import_data(self, textbuffer):
        '''Implements the actual import of the csv data'''
        textbuffer.insert(textbuffer.get_end_iter(), 'Importing registration data...\n')
        preregdata = []
        row = 1
        for reg in self.csvreg:
            tmpdict = {}
            for field in self.fields:
                value = self.fields_mapping[field](reg)
                if value and self.fieldsdic[field]['type'] == 'combobox':
                    if value not in self.fieldsdic[field]['options']:
                        optstr = '"' + '", "'.join(self.fieldsdic[field]['options']) + '", and blank'
                        errstr = """Error in csv row %d!
Found value "%s" in field "%s". Not a valid value!
Valid values (case sensitive) are: %s.
Correct the error and try again.""" % (row+1, value, field, optstr)
                        textbuffer.insert_with_tags_by_name(textbuffer.get_end_iter(), errstr, 'red')
                        return
                tmpdict[field] = value
            preregdata.append(tmpdict.copy())
            row += 1
        with open(os.path.join(self.cwd, self.path, self.path+'_registration_prereg.json'), 'w') as fout:
            json.dump(preregdata, fout, ensure_ascii=False)
        textbuffer.insert_with_tags_by_name(textbuffer.get_end_iter(), 'Success! Imported pre-registration saved to '+self.path+'_registration_prereg.json\nFinished!', 'blue')
