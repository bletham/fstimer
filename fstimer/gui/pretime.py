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
'''Handling of the window dedicated to selecting the timing dictionnary to be used'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import fstimer.gui
import os, json
from fstimer.gui.util_classes import GtkStockButton

class PreTimeWin(Gtk.Window):
    '''Handling of the window dedicated to selecting the timing dictionnary to be used'''

    def __init__(self, path, timing, okclicked_cb):
        '''Builds and display the compilation error window'''
        super(PreTimeWin, self).__init__(Gtk.WindowType.TOPLEVEL)
        self.path = path
        self.timing = timing
        self.okclicked_cb = okclicked_cb
        self.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        fname = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '../data/icon.png'))
        self.set_icon_from_file(fname)
        self.set_title('fsTimer - Project '+os.path.basename(self.path))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('delete_event', lambda b, jnk: self.hide())
        self.set_border_width(10)
        # Start with some intro text.
        btnFILE = Gtk.Button('Choose file')
        btnFILE.connect('clicked', self.choose_timingdict)
        self.pretimefilelabel = Gtk.Label(label='')
        self.pretimefilelabel.set_markup('<span color="blue">Select a timing dictionary.</span>')
        self.entry1 = Gtk.Entry()
        self.entry1.set_max_length(6)
        self.entry1.set_text('0')
        label2 = Gtk.Label('Specify a "pass" ID, not assigned to any racer')
        self.timebtncombobox = Gtk.ComboBoxText()
        self.timebtnlist = [' ', '.', '/']
        timebtndescr = ['Spacebar (" ")', 'Period (".")', 'Forward slash ("/")']
        for descr in timebtndescr:
          self.timebtncombobox.append_text(descr)
        self.timebtncombobox.set_active(0)
        label3 = Gtk.Label(label='Specify the key for marking times. It must not be in any of the IDs.')
        hbox3 = Gtk.HBox(False, 10)
        hbox3.pack_start(self.timebtncombobox, False, False, 8)
        hbox3.pack_start(label3, False, False, 8)
        btnCANCEL = GtkStockButton('close',"Close")
        btnCANCEL.connect('clicked', lambda b: self.hide())
        pretimebtnOK = GtkStockButton('ok',"OK")
        pretimebtnOK.connect('clicked', self.okclicked)
        btmhbox = Gtk.HBox(False, 8)
        btmhbox.pack_start(pretimebtnOK, False, False, 8)
        btmhbox.pack_start(btnCANCEL, False, False, 8)
        btmalign = Gtk.Alignment.new(1, 0, 0, 0)
        btmalign.add(btmhbox)
        hbox = Gtk.HBox(False, 10)
        hbox.pack_start(btnFILE, False, False, 8)
        hbox.pack_start(self.pretimefilelabel, False, False, 8)
        hbox2 = Gtk.HBox(False, 10)
        hbox2.pack_start(self.entry1, False, False, 8)
        hbox2.pack_start(label2, False, False, 8)
        vbox = Gtk.VBox(False, 10)
        vbox.pack_start(hbox, False, False, 8)
        vbox.pack_start(hbox2, False, False, 8)
        vbox.pack_start(hbox3, False, False, 8)
        vbox.pack_start(btmalign, False, False, 8)
        self.add(vbox)
        self.show_all()

    def choose_timingdict(self, jnk_unused):
        '''Handles click on Choose file button
           Converts the selected file into a defaultdict'''
        chooser = Gtk.FileChooserDialog(title='Choose timing dictionary', parent=self, action=Gtk.FileChooserAction.OPEN, buttons=('Cancel', Gtk.ResponseType.CANCEL, 'OK', Gtk.ResponseType.OK))
        chooser.set_current_folder(self.path)
        ffilter = Gtk.FileFilter()
        ffilter.set_name('Timing dictionaries')
        ffilter.add_pattern('*_timing_dict.json')
        chooser.add_filter(ffilter)
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = chooser.get_filename()
            self.timing.clear() # reset
            try:
                with open(filename, 'r', encoding='utf-8') as fin:
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
