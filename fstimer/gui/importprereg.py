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

import pygtk
pygtk.require('2.0')
import gtk
import fstimer.gui
import os, csv, json
import datetime

class ComboValueError(Exception):
    '''Exception launched when decoding reveals an invalid value for a combo field'''
    pass

class ImportPreRegWin(gtk.Window):
    '''Handling of the window dedicated to importation of pre-registration'''

    def __init__(self, cwd, path, fields, fieldsdic):
        '''Builds and display the importation window'''
        super(ImportPreRegWin, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.path = path
        self.cwd = cwd
        self.fields = fields
        self.fieldsdic = fieldsdic
        self.modify_bg(gtk.STATE_NORMAL, fstimer.gui.bgcolor)
        self.set_icon_from_file('fstimer/data/icon.png')
        self.set_title('fsTimer - ' + path)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', lambda b, jnk: self.hide())
        self.set_border_width(10)
        self.set_size_request(600, 400)
        # Start with some intro text.
        label1 = gtk.Label('Select a pre-registration csv file to import.')
        #Continue to the load file.
        btnFILE = gtk.Button(stock=gtk.STOCK_OPEN)
        ## Textbuffer
        textbuffer = gtk.TextBuffer()
        try:
            textbuffer.create_tag("blue", foreground="blue")
            textbuffer.create_tag("red", foreground="red")
        except TypeError:
            pass
        textview = gtk.TextView(textbuffer)
        textview.set_editable(False)
        textview.set_cursor_visible(False)
        textsw = gtk.ScrolledWindow()
        textsw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        textsw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        textsw.add(textview)
        textalgn = gtk.Alignment(0, 0, 1, 1)
        textalgn.add(textsw)
        hbox2 = gtk.HBox(False, 5)
        btnFILE.connect('clicked', self.select_preregistration, textbuffer)
        btn_algn = gtk.Alignment(1, 0, 1, 0)
        hbox2.pack_start(btnFILE, False, False, 0)
        hbox2.pack_start(btn_algn, True, True, 0)
        ## buttons
        btnOK = gtk.Button(stock=gtk.STOCK_OK)
        btnOK.connect('clicked', lambda b: self.hide())
        cancel_algn = gtk.Alignment(0, 0, 1, 0)
        hbox3 = gtk.HBox(False, 10)
        hbox3.pack_start(cancel_algn, True, True, 0)
        hbox3.pack_start(btnOK, False, False, 0)
        vbox = gtk.VBox(False, 0)
        vbox.pack_start(label1, False, False, 5)
        vbox.pack_start(hbox2, False, True, 5)
        vbox.pack_start(textalgn, True, True, 5)
        vbox.pack_start(hbox3, False, False, 0)
        self.add(vbox)
        self.show_all()

    def propose_advanced_import(self, csv_fields):
        '''Propose advanced import mechanism where project fields can be build
           from the csv ones using python expressions'''
        self.advancedwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.advancedwin.modify_bg(gtk.STATE_NORMAL, fstimer.gui.bgcolor)
        self.advancedwin.set_transient_for(self)
        self.advancedwin.set_modal(True)
        self.advancedwin.set_title('fsTimer - Advanced import')
        self.advancedwin.set_position(gtk.WIN_POS_CENTER)
        self.advancedwin.set_border_width(20)
        self.advancedwin.set_size_request(600, 400)
        self.advancedwin.connect('delete_event', lambda b, jnk_unused: self.advancedwin.hide())
        # top label
        toplabel = gtk.Label("Specify the mapping of csv fields to project ones.\n")
        # Treeview with 3 columns : field, combobox and free text
        self.fieldview = gtk.TreeView()
        self.fieldview.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        # Associated model with 5 columns : the 4th one is a boolean indicating
        # whether the 3rd one (Advanced mapping) should be sensitive
        self.fieldsmodel = gtk.ListStore(str, str, str, bool)
        for field in self.fields:
            self.fieldsmodel.append([field, field if field in csv_fields else '-- select --', '', False])
        self.fieldview.set_model(self.fieldsmodel)
        # build first column (project field)
        column = gtk.TreeViewColumn('Field', gtk.CellRendererText(), text=0)
        self.fieldview.append_column(column)
        # vuild 2nd column (csv field to be used, as a combo box)
        combo_renderer = gtk.CellRendererCombo()
        liststore_csv_fields = gtk.ListStore(str)
        liststore_csv_fields.append(['-- Leave empty --'])
        for field in csv_fields:
            liststore_csv_fields.append([field])
        liststore_csv_fields.append(['-- Advanced expression --'])
        combo_renderer.set_property("model", liststore_csv_fields)
        combo_renderer.set_property("text-column", 0)
        combo_renderer.set_property("editable", True)
        combo_renderer.set_property("has-entry", False)
        column = gtk.TreeViewColumn('CSV Column', combo_renderer, text=1)
        self.fieldview.append_column(column)
        # build the 3rd column (Advanced mapping)
        advanced_renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Advanced mapping', advanced_renderer, text=2, sensitive=3, editable=3)
        self.fieldview.append_column(column)
        # handler for the combo changes
        combo_renderer.connect("edited", self.combo_changed)
        advanced_renderer.connect("edited", self.text_changed)
        # And put it in a scrolled window, in an alignment
        fieldsw = gtk.ScrolledWindow()
        fieldsw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        fieldsw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        fieldsw.add(self.fieldview)
        fieldalgn = gtk.Alignment(0, 0, 1, 1)
        fieldalgn.add(fieldsw)
        # a text buffer for errors
        textbuffer = gtk.TextBuffer()
        try:
            textbuffer.create_tag("red", foreground="red")
            textbuffer.create_tag("blue", foreground="blue")
        except TypeError:
            pass
        textview = gtk.TextView(textbuffer)
        textview.set_editable(False)
        textview.set_cursor_visible(False)
        # hbox for the buttons
        hbox = gtk.HBox(False, 0)
        btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
        btnCANCEL.connect('clicked', lambda btn: self.advancedwin.hide())
        btnHELP = gtk.Button(stock=gtk.STOCK_HELP)#label='Avanced mapping _Help')
        btnHELP.connect('clicked', self.display_advanced_help)
        alignHELP = gtk.Alignment(.5, 0, .3, 0)
        alignHELP.add(btnHELP)
        btnOK = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        btnOK.connect('clicked', self.advanced_import_ok, textbuffer)
        alignOK = gtk.Alignment(1, 0, 0, 0)
        alignOK.add(btnOK)
        hbox.pack_start(btnCANCEL, False, True, 0)
        hbox.pack_start(alignHELP, True, True, 0)
        hbox.pack_start(alignOK, False, False, 0)
        # populate
        vbox = gtk.VBox(False, 10)
        vbox.pack_start(toplabel, False, False, 0)
        vbox.pack_start(fieldalgn, True, True, 0)
        vbox.pack_start(textview, False, False, 0)
        vbox.pack_start(hbox, False, False, 10)
        self.advancedwin.add(vbox)
        self.advancedwin.show_all()

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

    def display_advanced_help(self, jnk_unused):
        '''Displays Advanced mapping help'''
        help_dialog = gtk.MessageDialog(self, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE,
                                        'How to map CSV column(s) to a given field')
        help_dialog.format_secondary_markup('''For each field, 3 possibilities :
    - a CSV column to be mapped to the field
        <small>Note that columns with matching name are preselected</small>
    - '-- Leave Empty --' to leave field empty
    - '-- Advanced expression --' to use custom python expression

Expressions can combine values from several CSV columns.
Use the reg variable to refer to columns. It contains a dictionnary of column's name to column's value (as strings).

Here are examples for an Age and a Name column:
     %d - int(reg['Year of Birth'])
     ' '.join([reg['First name'], reg['Last name']])''' % datetime.date.today().year)
        help_dialog.set_title('Advanced mapping')
        help_dialog.connect('response', lambda btn, resp: help_dialog.hide())
        help_dialog.run()
        
    def advanced_import_ok(self, jnk_unused, textbuffer):
        '''Handles click on OK button in the advanced interface'''
        textbuffer.delete(textbuffer.get_start_iter(), textbuffer.get_end_iter())
        self.fields_mapping = {}
        for path in range(len(self.fieldsmodel)):
            field = self.fieldsmodel[path][0]
            csv_col = self.fieldsmodel[path][1]
            if csv_col == '-- select --':
                textbuffer.insert_with_tags_by_name(textbuffer.get_end_iter(), 'Nothing selected for field %s' % field, 'red')
                return
            elif csv_col == '-- Leave empty --':
                self.fields_mapping[field] = lambda reg, col=csv_col: ''
            elif csv_col == '-- Advanced expression --':
                try:
                    code = compile(self.fieldsmodel[path][2], '', 'eval')
                    self.fields_mapping[field] = lambda reg, code=code: eval(code)
                except SyntaxError, e:
                    iter_end = textbuffer.get_end_iter()
                    textbuffer.insert_with_tags_by_name(iter_end, 'Invalid syntax for expression of field %s' % field, 'red')
                    textbuffer.insert_with_tags_by_name(iter_end, str(e), 'blue')
                    return
            else:
                self.fields_mapping[field] = lambda reg, col=csv_col: reg[col]
        try:
            self.import_data(textbuffer)
            self.advancedwin.hide()
        except ComboValueError, e:
            textbuffer.insert_with_tags_by_name(textbuffer.get_end_iter(), str(e), 'red')
        except Exception, e:
            textbuffer.insert_with_tags_by_name(textbuffer.get_end_iter(), str(type(e)) + ' : ' + str(e), 'red')

    def build_fields_mapping(self, csv_fields, textbuffer):
        '''Maps cvs fields to project fields and creates a dictionnary
           of lambdas to apply to a csv entry to extract each field.
           Some entries may contain strings instead of lambdas, meaning
           that the project column's value is equal to that csv column's value'''
        iter_end = textbuffer.get_end_iter()
        fields_use = [field for field in csv_fields if field in self.fields]
        textbuffer.insert_with_tags_by_name(iter_end, 'Using csv fields: ', 'blue')
        textbuffer.insert(iter_end, ', '.join(fields_use) + os.linesep)
        fields_ignore = [field for field in csv_fields if field not in self.fields]
        textbuffer.insert_with_tags_by_name(iter_end, 'Ignoring csv fields: ', 'red')
        textbuffer.insert(iter_end, ', '.join(fields_ignore) + os.linesep)
        fields_notuse = [field for field in self.fields if field not in csv_fields]
        if fields_notuse:
            textbuffer.insert_with_tags_by_name(iter_end, 'Did not find: ', 'red')
            textbuffer.insert(iter_end, ', '.join(fields_notuse) + os.linesep)
            textbuffer.insert_with_tags_by_name(iter_end, 'Launching advanced interface', 'blue')
            self.propose_advanced_import(csv_fields)
        else:
            self.fields_mapping = {}
            for field in self.fields:
                self.fields_mapping[field] = lambda entry, field=field: entry[field]
            self.import_data(textbuffer)

    def select_preregistration(self, jnk_unused, textbuffer):
        '''Handle selection of a pre-reg file using a filechooser'''
        chooser = gtk.FileChooserDialog(title='Select pre-registration csv', action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
        ffilter = gtk.FileFilter()
        ffilter.set_name('csv files')
        ffilter.add_pattern('*.csv')
        chooser.add_filter(ffilter)
        chooser.set_current_folder(os.sep.join([self.cwd, self.path, '']))
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            textbuffer.set_text('Loading '+os.path.basename(filename)+'...\n')
            try:
                fin = csv.DictReader(open(filename, 'r'))
                self.csvreg = []
                for row in fin:
                    self.csvreg.append(row)
                csv_fields = self.csvreg[0].keys()
                iter_end = textbuffer.get_end_iter()
                textbuffer.insert_with_tags_by_name(iter_end, 'Found csv fields: ', 'blue')
                textbuffer.insert(iter_end, ', '.join(csv_fields) + os.linesep)
                self.build_fields_mapping(csv_fields, textbuffer)
            except (IOError, IndexError):
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
                        raise ComboValueError('''Error in csv row %d !
Found value "%s" in field "%s". Not a valid value!
Valid values (case sensitive) are: %s.
Correct the error and try again.''' % (row+1, value, field, optstr))
                tmpdict[field] = value
            preregdata.append(tmpdict.copy())
            row += 1
        with open(os.sep.join([self.cwd, self.path, self.path+'_registration_prereg.json']), 'wb') as fout:
            json.dump(preregdata, fout)
        textbuffer.insert_with_tags_by_name(textbuffer.get_end_iter(), 'Success! Imported pre-registration saved to '+self.path+'_registration_prereg.json\nFinished!', 'blue')
