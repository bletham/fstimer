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
'''Handling of the timing window'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import fstimer.gui
import fstimer.gui.editt0
import fstimer.gui.edittime
import fstimer.gui.editblocktimes
from fstimer.gui.register import RegistrationWin
import datetime
import time
import os
import re
import json
from gi.repository import Pango
from collections import defaultdict, Counter
from fstimer.gui.util_classes import MsgDialog
from fstimer.gui.GtkStockButton import GtkStockButton

class MergeError(Exception):
    '''Exception used in case of merging error'''
    pass

def time_format(t):
    '''formats time for display in the timing window'''
    milli = int((t - int(t)) * 10)
    hours, rem = divmod(int(t), 3600)
    minutes, seconds = divmod(rem, 60)
    if hours > 0:
        s = '%d:%02d:%02d.%01d' % (hours, minutes, seconds, milli)
    else:
        s = '%d:%02d.%01d' % (minutes, seconds, milli)
    return s

def time_parse(dt):
    '''converts string time to datetime.timedelta'''
    if dt and dt[0] == '-':
        return datetime.timedelta(0) #we don't allow negative times
    d = re.match(r'((?P<hours>\d+):)?(?P<minutes>\d+):(?P<seconds>\d+)(\.(?P<milliseconds>\d+))?', dt).groupdict(0)
    d['milliseconds'] = int(d['milliseconds'])*100  # they are actually centiseconds in the string
    return datetime.timedelta(**dict(((key, int(value)) for key, value in d.items())))

def time_diff(t1, t2):
    '''takes the diff of two string times and returns it as a time, rectified to 0. t1-t2.'''
    delta_t = time_parse(t1) - time_parse(t2)
    if delta_t < datetime.timedelta(0):
        return '0:00.0'
    else:
        return time_format(delta_t.total_seconds())

def time_sum(t1, t2):
    '''takes the sum of two string times and returns it as a time, t1+t2.'''
    timesum = time_parse(t1) + time_parse(t2)
    return time_format(timesum.total_seconds())

class TimingWin(Gtk.Window):
    '''Handling of the timing window'''

    def __init__(self, path, parent, timebtn, rawtimes, timing, print_cb, projecttype, numlaps,
                 fields, fieldsdic, write_timing_cb):
        '''Builds and display the compilation error window'''
        super(TimingWin, self).__init__(Gtk.WindowType.TOPLEVEL)
        self.path = path
        self.projecttype = projecttype
        self.fields = fields
        self.fieldsdic = fieldsdic
        self.write_timing_cb = write_timing_cb
        self.timebtn = timebtn
        self.rawtimes = rawtimes
        self.timing = timing
        self.numlaps = numlaps
        self.wineditblocktime = None
        self.winedittime = None
        self.t0win = None
        self.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title('fsTimer - ' + os.path.basename(path))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('delete_event', lambda b, jnk: self.done_timing(b))
        self.set_border_width(10)
        self.set_size_request(450, 450)
        # We will put the timing info in a liststore in a scrolledwindow
        self.timemodel = Gtk.ListStore(str, str)
        # We will put the liststore in a treeview
        self.timeview = Gtk.TreeView()
        column = Gtk.TreeViewColumn('ID', Gtk.CellRendererText(), text=0)
        self.timeview.append_column(column)
        column = Gtk.TreeViewColumn('Time', Gtk.CellRendererText(), text=1)
        self.timeview.append_column(column)
        #An extra column if it is a handicap race
        if projecttype == 'handicap':
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn('Corrected Time', renderer)
            column.set_cell_data_func(renderer, self.print_corrected_time)
            self.timeview.append_column(column)
        #Another extra column if it is a lap race
        if self.numlaps > 1:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn('Completed laps', renderer)
            column.set_cell_data_func(renderer, self.print_completed_laps)
            self.timeview.append_column(column)
        self.timeview.set_model(self.timemodel)
        self.timeview.connect('size-allocate', self.scroll_times)
        treeselection = self.timeview.get_selection()
        # make it multiple selecting
        treeselection.set_mode(Gtk.SelectionMode.MULTIPLE)
        # And put it in a scrolled window, in an alignment
        self.timesw = Gtk.ScrolledWindow()
        self.timesw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.timesw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.timesw.add(self.timeview)
        timealgn = Gtk.Alignment.new(0, 0, 1, 1)
        timealgn.add(self.timesw)
        self.entrybox = Gtk.Entry()
        self.entrybox.set_max_length(40)
        self.offset = 0 #this is len(times) - len(ids)
        self.entrybox.connect('activate', self.record_time)
        self.entrybox.connect('changed', self.check_for_newtime)
        # And we will save our file
        self.timestr = re.sub(' +', '_', time.ctime()).replace(':', '')
        #we save with the current time in the filename so no chance of being overwritten accidentally
        # Now lets go on to boxes
        tophbox = Gtk.HBox()
        # our default t0, and the stuff on top for setting/edit t0
        self.t0 = 0.
        btn_t0 = Gtk.Button('Start!')
        btn_t0.connect('clicked', self.set_t0)
        # time display
        self.clocklabel = Gtk.Label()
        self.clocklabel.modify_font(Pango.FontDescription("sans 20"))
        self.clocklabel.set_markup(time_format(0))
        tophbox.pack_start(btn_t0, False, False, 10)
        tophbox.pack_start(self.clocklabel, False, False, 10)
        timevbox1 = Gtk.VBox(False, 8)
        timevbox1.pack_start(tophbox, False, False, 0)
        timevbox1.pack_start(timealgn, True, True, 0)
        timevbox1.pack_start(Gtk.Label('Select box below in order to mark times:'), False, False, 0)
        timevbox1.pack_start(self.entrybox, False, False, 0)
        # we will keep track of how many racers are still out.
        self.racers_reg = []
        for i_unused in range(self.numlaps):
            self.racers_reg.append(set([k for k in timing.keys()]))
        self.racers_total = len(self.racers_reg[0])
        self.racers_in = [0] * self.numlaps
        self.lapcounter = defaultdict(int)
        self.racerslabel = Gtk.Label()
        self.update_racers_label()
        timevbox1.pack_start(self.racerslabel, False, False, 0)
        vbox1align = Gtk.Alignment.new(0, 0, 1, 1)
        vbox1align.add(timevbox1)
        # buttons on the right side
        #First an options button that will actually be a menu
        options_menu = Gtk.Menu()
        menu_editreg = Gtk.MenuItem('Edit registration data')
        menu_editreg.connect_object("activate", self.edit_reg, None)
        menu_editreg.show()
        options_menu.append(menu_editreg)
        menu_resett0 = Gtk.MenuItem('Restart clock')
        menu_resett0.connect_object("activate", self.restart_t0, None)
        menu_resett0.show()
        options_menu.append(menu_resett0)
        menu_editt0 = Gtk.MenuItem('Edit starting time')
        menu_editt0.connect_object("activate", self.edit_t0, None)
        menu_editt0.show()
        options_menu.append(menu_editt0)
        menu_savecsv = Gtk.MenuItem('Save results to CSV')
        menu_savecsv.connect_object("activate", print_cb, None, True) #True is to print csv
        menu_savecsv.show()
        options_menu.append(menu_savecsv)
        menu_resume = Gtk.MenuItem('Load saved timing session')
        menu_resume.connect_object("activate", self.resume_times, None, False) #False is for not merging
        menu_resume.show()
        options_menu.append(menu_resume)
        menu_merge = Gtk.MenuItem('Merge in saved IDs or times')
        menu_merge.connect_object("activate", self.resume_times, None, True) #True is for merging
        menu_merge.show()
        options_menu.append(menu_merge)
        btnOPTIONS = Gtk.Button('Options')
        btnOPTIONS.connect_object("event", self.options_btn, options_menu)
        options_align = Gtk.Alignment.new(1, 0.1, 1, 0)
        options_align.add(btnOPTIONS)
        #Then the block of editing buttons
        btnDROPID = Gtk.Button('Drop ID')
        btnDROPID.connect('clicked', self.timing_rm_ID)
        btnDROPTIME = Gtk.Button('Drop time')
        btnDROPTIME.connect('clicked', self.timing_rm_time)
        btnEDIT = GtkStockButton(Gtk.STOCK_EDIT,"Edit")
        btnEDIT.connect('clicked', self.edit_time)
        edit_vbox = Gtk.VBox(True, 8)
        edit_vbox.pack_start(btnDROPID, False, False, 0)
        edit_vbox.pack_start(btnDROPTIME, False, False, 0)
        edit_vbox.pack_start(btnEDIT, False, False, 0)
        edit_align = Gtk.Alignment.new(1, 0, 1, 0)
        edit_align.add(edit_vbox)
        #Then the print and save buttons
        btnPRINT = Gtk.Button('Printouts')
        btnPRINT.connect('clicked', print_cb, False)
        btnSAVE = GtkStockButton(Gtk.STOCK_SAVE,"Save")
        btnSAVE.connect('clicked', self.save_times)
        save_vbox = Gtk.VBox(True, 8)
        save_vbox.pack_start(btnPRINT, False, False, 0)
        save_vbox.pack_start(btnSAVE, False, False, 0)
        save_align = Gtk.Alignment.new(1, 1, 1, 0)
        save_align.add(save_vbox)
        #And finally the finish button
        btnOK = GtkStockButton(Gtk.STOCK_CLOSE,"Close")
        btnOK.connect('clicked', self.done_timing)
        done_align = Gtk.Alignment.new(1, 0.7, 1, 0)
        done_align.add(btnOK)
        vsubbox = Gtk.VBox(True, 0)
        vsubbox.pack_start(options_align, True, True, 0)
        vsubbox.pack_start(edit_align, True, True, 0)
        vsubbox.pack_start(save_align, True, True, 0)
        vsubbox.pack_start(done_align, True, True, 0)
        vspacer = Gtk.Alignment.new(1, 1, 0, 0)
        vspacer.add(vsubbox)
        timehbox = Gtk.HBox(False, 8)
        timehbox.pack_start(vbox1align, True, True, 0)
        timehbox.pack_start(vspacer, False, False, 0)
        self.add(timehbox)
        self.show_all()

    def print_corrected_time(self, column, renderer, model, itr, data):
        '''computes a handicap corrected time from en entry in the timing model'''
        bibid, st = model.get(itr, 0, 1)
        if st and self.timing[bibid]['Handicap']:
            try:
                nt = time_diff(st, self.timing[bibid]['Handicap'])
                renderer.set_property('text', nt)
            except AttributeError:
                #Handicap is present but is not formatted correctly.
                renderer.set_property('text', '')
        else:
            renderer.set_property('text', '')

    def print_completed_laps(self, column, renderer, model, itr, data):
        '''computes number of laps completed by this (registered) racer'''
        bibid, st = model.get(itr, 0, 1)
        if bibid:
            renderer.set_property('text', str(self.lapcounter[bibid]))
        else:
            renderer.set_property('text', '')

    def update_racers_label(self):
        '''update values in the racers_label'''
        s = '%d registrants. Checked in' % self.racers_total
        if self.numlaps > 1:
            s += ' (per lap)'
        s += ': ' + ' | '.join(str(n) for n in self.racers_in)
        self.racerslabel.set_markup(s)

    def check_for_newtime(self, jnk_unused):
        '''Handles entering of a new time'''
        if self.entrybox.get_text() == self.timebtn:
            self.new_blank_time()

    def scroll_times(self, jnk1_unused, jnk2_unused):
        '''handles scrolling of the time window'''
        adj = self.timesw.get_vadjustment()
        adj.set_value(0)

    def update_clock(self):
        '''Updates the clock'''
        # compute time
        t = time.time()-self.t0
        # update label
        self.clocklabel.set_markup(time_format(t))
        # keep updating
        return True

    def set_t0(self, btn):
        '''Handles click on Start button
           Sets t0 to the current time'''
        self.t0 = time.time()
        GLib.timeout_add(100, self.update_clock) #update clock every 100ms
        btn.set_sensitive(False)

    def restart_t0(self, jnk_unused):
        '''Handles click on restart clock button'''
        restart_t0_dialog = MsgDialog(self, 'warning', 'YES_NO', 'Are you sure?', 
                                      'Are you sure you want to restart the race clock?\nThis cannot be undone.')
        restart_t0_dialog.set_default_response(Gtk.ResponseType.NO)
        response = restart_t0_dialog.run()
        restart_t0_dialog.destroy()
        if response == Gtk.ResponseType.YES:
            self.t0 = time.time()
    
    def edit_t0(self, jnk_unused):
        '''Handles click on Edit button for the t0 value.
           Loads up a window and query the new t0'''
        self.t0win = fstimer.gui.editt0.EditT0Win(self.path, self, self.t0, self.ok_editt0)

    def ok_editt0(self, t0):
        '''Handles click on OK after t0 edition'''
        self.t0 = t0
        self.t0win.hide()

    def options_btn(self, menu, event):
        '''Handles opening the menu on click of the options button'''
        if event.type == Gdk.EventType.BUTTON_PRESS:
            menu.popup(parent_menu_shell=None,parent_menu_item=None, func=None, data=None, button=event.get_button()[1], activate_time=event.get_time())
            return True
        else:
            return False

    def edit_reg(self, jnk_unused):
        filename = os.path.join(self.path, os.path.basename(self.path)+'_registration_compiled.json')
        with open(filename, 'r', encoding='utf-8') as fin:
            self.reg_file = json.load(fin)
        regwin = RegistrationWin(
            self.path, self.fields, self.fieldsdic, self.reg_file, self.projecttype, self.save_reg, self, False,
            'Loaded '+filename)
    
    def save_reg(self):
        # Re-create the timing dictionary
        timedict = defaultdict(lambda: defaultdict(str))
        for reg in self.reg_file:
            # Any registration without an ID is left out of the timing dictionary
            if reg['ID']:
                # have we already added this ID to the timing dictionary?
                if reg['ID'] in timedict.keys():
                    return 'ID {} NOT UNIQUE'.format(reg['ID']), False
                else:
                    timedict[reg['ID']] = reg
        # Write the files and set the new timedict
        filename = self.write_timing_cb(self.reg_file, timedict)
        return filename, True
    
    def edit_time(self, jnk_unused):
        '''Handles click on Edit button for a time
           Chooses which edit time window to open,
           depending on how many items are selected'''
        treeselection = self.timeview.get_selection()
        pathlist = treeselection.get_selected_rows()[1]
        if len(pathlist) == 0:
            # we don't load any windows or do anything
            pass
        elif len(pathlist) == 1:
            # load the edit_single window
            treeiter = self.timemodel.get_iter(pathlist[0])
            old_id, old_time = self.timemodel.get(treeiter, 0, 1)
            self.winedittime = fstimer.gui.edittime.EditTimeWin \
                (self, old_id, old_time,
                 lambda id, time: self.editsingletimedone(treeiter, id, time))
        else:
            self.wineditblocktime = fstimer.gui.editblocktimes.EditBlockTimesWin \
                (self, lambda op, time: self.editblocktimedone(pathlist, op, time))
        return

    def editsingletimedone(self, treeiter, new_id, new_time):
        '''Handled result of the editing of a given time'''
        row = self.timemodel.get_path(treeiter)[0]
        if not re.match('^[0-9:.]*$', new_time):
            md = MsgDialog(self, 'error', 'OK', 'Error!', 'Time is not valid format.')
            md.run()
            md.destroy()
            return
        if row < self.offset:
            if new_id:
                # we are putting an ID in a slot that we hadn't reached yet
                # Fill in any other missing ones up to this point with ''.
                ids = [str(new_id)]
                ids.extend(['' for i_unused in range(self.offset-row-1)])
                ids.extend(self.rawtimes['ids'])
                self.rawtimes['ids'] = list(ids)
                self.offset = row #the new offset
                self.rawtimes['times'][row] = str(new_time) #the new time
                self.timemodel.set_value(treeiter, 0, str(new_id))
                self.timemodel.set_value(treeiter, 1, str(new_time))
            elif new_time:
                # we are adjusting the time only.
                self.rawtimes['times'][row] = str(new_time) #the new time
                self.timemodel.set_value(treeiter, 1, str(new_time))
            else:
                # we are clearing this entry. pop it from time and adjust offset.
                self.rawtimes['times'].pop(row)
                self.offset -= 1
                self.timemodel.remove(treeiter)
        elif row == self.offset and new_time and not new_id:
            # then we are clearing the most recent ID.
            # We pop it and adjust self.offset and adjust the time.
            self.rawtimes['ids'].pop(0)
            self.rawtimes['times'][row] = str(new_time)
            self.offset += 1
            self.timemodel.set_value(treeiter, 0, str(new_id))
            self.timemodel.set_value(treeiter, 1, str(new_time))
        elif row < -self.offset:
            # Here we are making edits to a slot where there is an ID, but no time.
            if new_time:
                #we are putting a time in a slot that we hadn't reached yet. Fill in any other missing ones up to this point with blanks.
                times = [str(new_time)]
                times.extend(['' for i_unused in range(-self.offset-row-1)])
                times.extend(self.rawtimes['times'])
                self.rawtimes['times'] = list(times)
                self.offset = -row #the new offset
                self.rawtimes['ids'][row] = str(new_id) #the new time
                self.timemodel.set_value(treeiter, 0, str(new_id))
                self.timemodel.set_value(treeiter, 1, str(new_time))
            elif new_id:
                #we are adjusting the id only.
                self.rawtimes['ids'][row] = str(new_id) #the new time
                self.timemodel.set_value(treeiter, 0, str(new_id))
            else:
                #we are clearing this entry. pop it from id and adjust offset.
                self.rawtimes['ids'].pop(row)
                self.offset += 1
                self.timemodel.remove(treeiter)
        else:
            if not new_time and not new_id:
                # we are clearing the entry
                if self.offset > 0:
                    self.rawtimes['ids'].pop(row-self.offset)
                    self.rawtimes['times'].pop(row)
                elif self.offset <= 0:
                    self.rawtimes['ids'].pop(row)
                    self.rawtimes['times'].pop(row+self.offset)
                self.timemodel.remove(treeiter)
            else:
                # adjust the entry; no changes to the stack otherwise.
                if self.offset > 0:
                    self.rawtimes['ids'][row-self.offset] = str(new_id)
                    self.rawtimes['times'][row] = str(new_time)
                elif self.offset <= 0:
                    self.rawtimes['ids'][row] = str(new_id)
                    self.rawtimes['times'][row+self.offset] = str(new_time)
                self.timemodel.set_value(treeiter, 0, str(new_id))
                self.timemodel.set_value(treeiter, 1, str(new_time))
        #reset lapcounter, if used..
        if self.numlaps > 1:
            self.lapcounter = defaultdict(int)
            self.lapcounter.update(Counter(self.rawtimes['ids']))
        self.winedittime.hide()

    def editblocktimedone(self, pathlist, operation, timestr):
        '''Handled result of the editing of a block of times
           Goes through every time in pathlist and do the requested operation'''
        for gtkpath in pathlist:
            # Figure out which row this is, and which treeiter
            treeiter = self.timemodel.get_iter(gtkpath)
            row = gtkpath[0]
            # Now figure out the new time. First get the old time as a string
            old_time_str = self.timemodel.get_value(treeiter, 1)
            try:
                if operation == 'ADD':
                    new_time = time_sum(old_time_str, timestr)
                elif operation == 'SUBTRACT':
                    new_time = time_diff(old_time_str, timestr)
                # Save them, and write out to the timemodel
                self.rawtimes['times'][row] = str(new_time)
                self.timemodel.set_value(treeiter, 1, str(new_time))
            except AttributeError:
                # This will happen for instance if the gtkpath has a blank time
                pass
        self.wineditblocktime.hide()

    def timing_rm_ID(self, jnk_unused):
        '''Handles click on the Drop ID button
           Throws up an 'are you sure' dialog box, and drop if yes.'''
        treeselection = self.timeview.get_selection()
        pathlist = treeselection.get_selected_rows()[1]
        if len(pathlist) == 0:
            # we don't load any windows or do anything
            pass
        elif len(pathlist) > 1:
            # this is a one-at-a-time operation
            pass
        elif len(pathlist) == 1:
            # Figure out what row this is in the timeview
            row = pathlist[0][0]
            # Now figure out what index in self.rawtimes['ids'] it is.
            ididx = row-max(0, self.offset)
            if ididx >= 0:
                # Otherwise, there is no ID here so there is nothing to do.
                # Ask if we are sure.
                rmID_dialog = MsgDialog(self, 'warning', 'YES_NO', 'Are you sure?', 'Are you sure you want to drop this ID and shift all later IDs down earlier in the list?\nThis cannot be undone.')
                rmID_dialog.set_default_response(Gtk.ResponseType.NO)
                response = rmID_dialog.run()
                rmID_dialog.destroy()
                if response == Gtk.ResponseType.YES:
                    # Make the shift in self.rawtimes and self.offset
                    self.rawtimes['ids'].pop(ididx)
                    self.offset += 1
                    # And now shift everything on the display.
                    rowcounter = int(row)
                    for i in range(ididx-1, -1, -1):
                        # Write rawtimes[i] into row rowcounter
                        treeiter = self.timemodel.get_iter((rowcounter,))
                        self.timemodel.set_value(treeiter, 0, str(self.rawtimes['ids'][i]))
                        rowcounter -= 1
                    # Now we tackle the last value - there are two possibilities.
                    if self.offset > 0:
                        # There is a buffer of times, and this one should be cleared.
                        treeiter = self.timemodel.get_iter((rowcounter,))
                        self.timemodel.set_value(treeiter, 0, '')
                    else:
                        # There is a blank row at the top which should be removed.
                        treeiter = self.timemodel.get_iter((rowcounter,))
                        self.timemodel.remove(treeiter)

    def timing_rm_time(self, jnk_unused):
        '''Handles click on Drop time comment
           Throws up an 'are you sure' dialog box, and drop if yes.'''
        treeselection = self.timeview.get_selection()
        pathlist = treeselection.get_selected_rows()[1]
        if len(pathlist) == 0:
            # we don't load any windows or do anything
            pass
        elif len(pathlist) > 1:
            # this is a one-at-a-time operation
            pass
        elif len(pathlist) == 1:
            # Figure out what row this is in the timeview
            row = pathlist[0][0]
            # Now figure out what index in self.rawtimes['times'] it is.
            timeidx = row-max(0, -self.offset)
            if timeidx >= 0:
                # Otherwise, there is no time here so there is nothing to do.
                # Ask if we are sure.
                rmtime_dialog = MsgDialog(self, 'warning', 'YES_NO', 'Are you sure?', 'Are you sure you want to drop this time and shift all later times down earlier in the list?\nThis cannot be undone.')
                rmtime_dialog.set_default_response(Gtk.ResponseType.NO)
                response = rmtime_dialog.run()
                rmtime_dialog.destroy()
                if response == Gtk.ResponseType.YES:
                    # Make the shift in self.rawtimes and self.offset
                    self.rawtimes['times'].pop(timeidx)
                    self.offset -= 1
                    # And now shift everything on the display.
                    rowcounter = int(row)
                    for i in range(timeidx-1, -1, -1):
                        # Write rawtimes[i] into row rowcounter
                        treeiter = self.timemodel.get_iter((rowcounter,))
                        self.timemodel.set_value(treeiter, 1, str(self.rawtimes['times'][i]))
                        rowcounter -= 1
                    # Now we tackle the last value - there are two possibilities.
                    if self.offset < 0:
                        # There is a buffer of IDs, and this one should be cleared.
                        treeiter = self.timemodel.get_iter((rowcounter,))
                        self.timemodel.set_value(treeiter, 1, '')
                    else:
                        # there is a blank row at the top which should be removed.
                        treeiter = self.timemodel.get_iter((rowcounter,))
                        self.timemodel.remove(treeiter)

    def resume_times(self, jnk_unused, isMerge):
        '''Handles click on Resume button'''
        chooser = Gtk.FileChooserDialog(title='Choose timing results to resume', parent=self, action=Gtk.FileChooserAction.OPEN, buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
        chooser.set_current_folder(self.path)
        ffilter = Gtk.FileFilter()
        ffilter.set_name('Timing results')
        ffilter.add_pattern('*_times.json')
        chooser.add_filter(ffilter)
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = chooser.get_filename()
            try:
                with open(filename, 'r', encoding='utf-8') as fin:
                    saveresults = json.load(fin)
                newrawtimes = saveresults['rawtimes']
                if isMerge:
                    if self.rawtimes['ids'] and not self.rawtimes['times']:
                        if newrawtimes['times'] and not newrawtimes['ids']:
                            #Merge! We have IDs, merge in times.
                            self.rawtimes['times'] = list(newrawtimes['times'])
                        else:
                            raise MergeError('Must be pure IDs merged into pure times, or vice versa')
                    elif self.rawtimes['times'] and not self.rawtimes['ids']:
                        if newrawtimes['ids'] and not newrawtimes['times']:
                            #Merge! We have times, merge in IDS.
                            self.rawtimes['ids'] = list(newrawtimes['ids'])
                        else:
                            raise MergeError('Must be pure IDs merged into pure times, or vice versa')
                    else:
                        raise MergeError('Must be pure IDs merged into pure times, or vice versa')
                else:
                    self.rawtimes['ids'] = newrawtimes['ids']
                    self.rawtimes['times'] = newrawtimes['times']
                    #self.timestr = saveresults['timestr'] #We will _not_ overwrite when resuming.
                    self.t0 = saveresults['t0']
                    GLib.timeout_add(100, self.update_clock) #start the stopwatch
                # Recompute how many racers have checked in
                self.racers_in = [0] * self.numlaps
                for ID in self.rawtimes['ids']:
                    self.update_racers(ID)
                self.offset = len(self.rawtimes['times']) - len(self.rawtimes['ids'])
                # Update racers' label
                self.update_racers_label()
                self.timemodel.clear()
                if self.offset >= 0:
                    adj_ids = ['' for i_unused in range(self.offset)]
                    adj_ids.extend(self.rawtimes['ids'])
                    adj_times = list(self.rawtimes['times'])
                elif self.offset < 0:
                    adj_times = ['' for i_unused in range(-self.offset)]
                    adj_times.extend(self.rawtimes['times'])
                    adj_ids = list(self.rawtimes['ids'])
                for entry in zip(adj_ids, adj_times):
                    self.timemodel.append(list(entry))
            except (IOError, ValueError, TypeError, MergeError) as e:
                error_dialog = MsgDialog(self, 'error', 'OK', 'Oops...', 'ERROR: Failed to %s : %s.' % ('merge' if isMerge else 'resume', e))
                response = error_dialog.run()
                error_dialog.destroy()
        chooser.destroy()

    def save_times(self, jnk_unused):
        '''Handles click on the Save button
           jsonn dump to the already specified filename'''
        saveresults = {}
        saveresults['rawtimes'] = self.rawtimes
        saveresults['timestr'] = self.timestr
        saveresults['t0'] = self.t0
        with open(os.path.join(self.path, os.path.basename(self.path)+'_'+self.timestr+'_times.json'), 'w', encoding='utf-8') as fout:
            json.dump(saveresults, fout)
        md = MsgDialog(self, 'information', 'OK', 'Saved!', 'Times saved!')
        md.run()
        md.destroy()

    def done_timing(self, source):
        '''Handles click on the Done button
           Gives a dialog before closing.'''
        oktime_dialog2 = MsgDialog(self, 'question', 'YES_NO_CANCEL', 'Save?', 'Do you want to save before finishing?\nUnsaved data will be lost.')
        response2 = oktime_dialog2.run()
        oktime_dialog2.destroy()
        if response2 == Gtk.ResponseType.CANCEL:
            return
        elif response2 == Gtk.ResponseType.YES:
            self.save_times(None)
        self.hide()

    def update_racers(self, ID):
        '''Updates racers_reg and racers_in after arrival of user ID'''
        self.lapcounter[ID] += 1
        for i in range(self.numlaps):
            if ID in self.racers_reg[i]:
                self.racers_reg[i].remove(ID)
                self.racers_in[i] += 1
                break

    def record_time(self, jnk_unused):
        '''Handles a hit on enter in the entry box.
           An ID with times in the buffer gives the oldest (that is, fastest)
           time in the buffer to the ID
           An ID with no times in the buffer is added to a buffer of IDs
           An ID with the marktime symbol in it will first apply the ID
           and then mark the time.'''
        txt = self.entrybox.get_text()
        timemarks = txt.count(self.timebtn)
        txt = txt.replace(self.timebtn, '')
        # it is actually a result. (or a pass, which we treat as a result)
        # prepend to raw
        self.rawtimes['ids'].insert(0, txt)
        # add to the appropriate spot on timemodel.
        if self.offset > 0:
            # we have a time in the store to assign it to
             # put it in the last available time slot
            self.timemodel.set_value(self.timemodel.get_iter(self.offset-1), 0, txt)
        else:
            # It will just be added to the buffer of IDs by prepending to timemodel
            self.timemodel.prepend([txt, ''])
        self.offset -= 1
        for jnk_unused in range(timemarks):
            self.new_blank_time()
        # update the racer count.
        try:
            self.update_racers(txt)
            self.update_racers_label()
        except ValueError:
            pass
        self.entrybox.set_text('')

    def new_blank_time(self):
        '''Record a new time'''
        t = time_format(time.time()-self.t0)
        self.rawtimes['times'].insert(0, t) #we prepend to rawtimes, just as we prepend to timemodel
        if self.offset >= 0:
            # No IDs in the buffer, so just prepend it to the liststore.
            self.timemodel.prepend(['', t])
        elif self.offset < 0:
            # IDs in the buffer, so add the time to the oldest ID
            # put it in the last available ID slot
            self.timemodel.set_value(self.timemodel.get_iter(-self.offset-1), 1, t)
        self.offset += 1
        self.entrybox.set_text('')
