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
'''Handling of the window dedicated to selecting the timing dictionnary to be used'''

import pygtk
pygtk.require('2.0')
import gtk
import fstimer.gui
import os, json

class PreTimeWin(gtk.Window):
    '''Handling of the window dedicated to selecting the timing dictionnary to be used'''

    def __init__(self, path, timing, okclicked_cb):
        '''Builds and display the compilation error window'''
        super(PreTimeWin, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.path = path
        self.timing = timing
        self.okclicked_cb = okclicked_cb
        self.modify_bg(gtk.STATE_NORMAL, fstimer.gui.bgcolor)
        self.set_icon_from_file('fstimer/data/icon.png')
        self.set_title('fsTimer - Project '+self.path)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', lambda b, jnk: self.hide())
        self.set_border_width(10)
        # Start with some intro text.
        btnFILE = gtk.Button('Choose file')
        btnFILE.connect('clicked', self.choose_timingdict)
        self.pretimefilelabel = gtk.Label('')
        self.pretimefilelabel.set_markup('<span color="blue">Select a timing dictionary.</span>')
        self.entry1 = gtk.Entry(max=6)
        self.entry1.set_text('0')
        label2 = gtk.Label('Specify a "pass" ID, not assigned to any racer')
        self.timebtncombobox = gtk.combo_box_new_text()
        self.timebtnlist = [' ', '.', '/']
        timebtndescr = ['Spacebar (" ")', 'Period (".")', 'Forward slash ("/")']
        for descr in timebtndescr:
          self.timebtncombobox.append_text(descr)
        self.timebtncombobox.set_active(0)
        label3 = gtk.Label('Specify the key for marking times. It must not be in any of the IDs.')
        hbox3 = gtk.HBox(False, 10)
        hbox3.pack_start(self.timebtncombobox, False, False, 8)
        hbox3.pack_start(label3, False, False, 8)
        btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
        btnCANCEL.connect('clicked', lambda b: self.hide())
        pretimebtnOK = gtk.Button(stock=gtk.STOCK_OK)
        pretimebtnOK.connect('clicked', self.okclicked)
        btmhbox = gtk.HBox(False, 8)
        btmhbox.pack_start(pretimebtnOK, False, False, 8)
        btmhbox.pack_start(btnCANCEL, False, False, 8)
        btmalign = gtk.Alignment(1, 0, 0, 0)
        btmalign.add(btmhbox)
        hbox = gtk.HBox(False, 10)
        hbox.pack_start(btnFILE, False, False, 8)
        hbox.pack_start(self.pretimefilelabel, False, False, 8)
        hbox2 = gtk.HBox(False, 10)
        hbox2.pack_start(self.entry1, False, False, 8)
        hbox2.pack_start(label2, False, False, 8)
        vbox = gtk.VBox(False, 10)
        vbox.pack_start(hbox, False, False, 8)
        vbox.pack_start(hbox2, False, False, 8)
        vbox.pack_start(hbox3, False, False, 8)
        vbox.pack_start(btmalign, False, False, 8)
        self.add(vbox)
        self.show_all()

    def choose_timingdict(self, jnk_unused):
        '''Handles click on Choose file button
           Converts the selected file into a defaultdict'''
        chooser = gtk.FileChooserDialog(title='Choose timing dictionary', action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
        chooser.set_current_folder(os.sep.join([os.getcwd(), self.path]))
        ffilter = gtk.FileFilter()
        ffilter.set_name('Timing dictionaries')
        ffilter.add_pattern('*_timing_dict.json')
        chooser.add_filter(ffilter)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            self.timing.clear() # reset
            try:
                with open(filename, 'rb') as fin:
                  a = json.load(fin)
                for reg in a.keys():
                  self.timing[reg].update(a[reg])
                self.pretimefilelabel.set_markup('<span color="blue">'+os.path.basename(filename)+' loaded.</span>')
            except (IOError, ValueError):
                self.pretimefilelabel.set_markup('<span color="red">ERROR! '+os.path.basename(filename)+' not valid.</span>')
        chooser.destroy()

    def okclicked(self, jnk_unused):
        '''Handles click on ok button'''
        passid = self.entry1.get_text()
        timebtn = self.timebtnlist[self.timebtncombobox.get_active()]
        self.okclicked_cb(passid, timebtn)
