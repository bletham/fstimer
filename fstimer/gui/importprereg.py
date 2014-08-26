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
                csvreg = []
                for row in fin:
                    csvreg.append(row)
                csv_fields = csvreg[0].keys()
                try:
                    textbuffer.create_tag("blue", foreground="blue")
                    textbuffer.create_tag("red", foreground="red")
                except TypeError:
                    pass
                printstr = 'Found csv fields: '
                if csv_fields:
                    for field in csv_fields:
                        printstr += field + ', '
                    printstr = printstr[:-2]
                printstr += '\n'
                iter1 = textbuffer.get_end_iter()
                textbuffer.insert(iter1, printstr)
                iter1 = textbuffer.get_iter_at_line(1)
                iter2 = textbuffer.get_iter_at_line_offset(1, 17)
                textbuffer.apply_tag_by_name("blue", iter1, iter2)
                printstr = 'Using csv fields: '
                fields_use = [field for field in csv_fields if field in self.fields]
                if fields_use:
                    for field in fields_use:
                        printstr += field + ', '
                    printstr = printstr[:-2]
                printstr += '\n'
                iter1 = textbuffer.get_end_iter()
                textbuffer.insert(iter1, printstr)
                iter1 = textbuffer.get_iter_at_line(2)
                iter2 = textbuffer.get_iter_at_line_offset(2, 17)
                textbuffer.apply_tag_by_name("blue", iter1, iter2)
                printstr = 'Ignoring csv fields: '
                fields_ignore = [field for field in csv_fields if field not in self.fields]
                if fields_ignore:
                    for field in fields_ignore:
                        printstr += field + ', '
                    printstr = printstr[:-2]
                printstr += '\n'
                iter1 = textbuffer.get_end_iter()
                textbuffer.insert(iter1, printstr)
                iter1 = textbuffer.get_iter_at_line(3)
                iter2 = textbuffer.get_iter_at_line_offset(3, 20)
                textbuffer.apply_tag_by_name("red", iter1, iter2)
                printstr = 'Did not find: '
                fields_notuse = [field for field in self.fields if field not in csv_fields]
                if fields_notuse:
                    for field in fields_notuse:
                        printstr += field + ', '
                    printstr = printstr[:-2]
                printstr += '\n'
                iter1 = textbuffer.get_end_iter()
                textbuffer.insert(iter1, printstr)
                iter1 = textbuffer.get_iter_at_line(4)
                iter2 = textbuffer.get_iter_at_line_offset(4, 13)
                textbuffer.apply_tag_by_name("red", iter1, iter2)
                iter1 = textbuffer.get_end_iter()
                textbuffer.insert(iter1, 'Importing registration data...\n')
                preregdata = []
                breakloop = 0
                row = 1
                for reg in csvreg:
                    if breakloop == 0:
                        tmpdict = {}
                        for field in fields_notuse:
                            tmpdict[field] = ''
                        for field in fields_use:
                            if self.fieldsdic[field]['type'] == 'combobox':
                                if reg[field] and reg[field] not in self.fieldsdic[field]['options']:
                                    breakloop = 1
                                    optstr = ''
                                    for opt in self.fieldsdic[field]['options']:
                                        optstr += '"' + opt + '", '
                                    optstr += 'and blank'
                                    iter1 = textbuffer.get_end_iter()
                                    textbuffer.insert(iter1, '''Error in csv row %d ! Found value "%s" in field "%s". Not a valid value!
Valid values (case sensitive) are: %s.
Nothing was imported. Correct the error and try again.''' % (row+1, reg[field], field, optstr))
                                    iter1 = textbuffer.get_iter_at_line(6)
                                    iter2 = textbuffer.get_end_iter()
                                    textbuffer.apply_tag_by_name("red", iter1, iter2)
                            tmpdict[field] = str(reg[field])
                        preregdata.append(tmpdict.copy())
                        row += 1
                if breakloop == 0:
                    with open(os.sep.join([self.cwd, self.path, self.path+'_registration_prereg.json']), 'wb') as fout:
                        json.dump(preregdata, fout)
                    iter1 = textbuffer.get_end_iter()
                    textbuffer.insert(iter1, 'Success! Imported pre-registration saved to '+self.path+'_registration_prereg.json\nFinished!')
                    iter1 = textbuffer.get_iter_at_line(6)
                    iter2 = textbuffer.get_end_iter()
                    textbuffer.apply_tag_by_name("blue", iter1, iter2)
            except (IOError, IndexError):
                iter1 = textbuffer.get_end_iter()
                try:
                    textbuffer.create_tag("red", foreground="red")
                except TypeError:
                    pass
                textbuffer.insert(iter1, 'Error! Could not open file, or no data found in file. Nothing was imported, try again.')
                iter1 = textbuffer.get_iter_at_line(1)
                iter2 = textbuffer.get_end_iter()
                textbuffer.apply_tag_by_name("red", iter1, iter2)
        chooser.destroy()
