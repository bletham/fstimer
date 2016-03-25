#!/usr/bin/env python3

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

'''Main class of the fsTimer package'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os, json, csv, re, datetime
from os.path import normpath, join, dirname, abspath, basename
import fstimer.gui.intro
import fstimer.gui.newproject
import fstimer.gui.projecttype
import fstimer.gui.definefields
import fstimer.gui.definefamilyreset
import fstimer.gui.definedivisions
import fstimer.gui.root
import fstimer.gui.about
import fstimer.gui.importprereg
import fstimer.gui.preregister
import fstimer.gui.register
import fstimer.gui.compile
import fstimer.gui.compileerrors
import fstimer.gui.pretime
import fstimer.gui.timing
import fstimer.printcsv
import fstimer.printcsvlaps
import fstimer.printhtml
import fstimer.printhtmllaps
from fstimer.gui.timing import time_diff
from collections import defaultdict
from fstimer.gui.util_classes import MsgDialog


class PyTimer(object):
    '''main class of fsTimer'''

    def __init__(self):
        '''constructor method. Displays top level window'''
        self.introwin = fstimer.gui.intro.IntroWin(self.load_project,
                                                   self.create_project)

    def load_project(self, jnk_unused, combobox, projectlist):
        '''Loads the registration settings of a project, and go back to rootwin'''
        self.projectname = projectlist[combobox.get_active()]
        self.path = normpath(join(dirname(dirname(abspath(__file__))),self.projectname))
        #self.path is now _absolute_, it is not project name.
        with open(os.path.join(self.path, self.projectname+'.reg'), 'r', encoding='utf-8') as fin:
            regdata = json.load(fin)
        #Assign all of the project settings
        self.fields = regdata['fields']
        self.fieldsdic = regdata['fieldsdic']
        self.clear_for_fam = regdata['clear_for_fam']
        self.divisions = regdata['divisions']
        try:
            self.projecttype = regdata['projecttype']
        except KeyError:
            # old project, with no type, type is thus standard one
            self.projecttype = 'standard'
        try:
            self.numlaps = regdata['numlaps']
        except KeyError:
            self.numlaps = 1
        #Move on to the main window
        self.introwin.hide()
        self.rootwin = fstimer.gui.root.RootWin(self.path,
                                                self.show_about,
                                                self.import_prereg,
                                                self.handle_preregistration,
                                                self.compreg_window,
                                                self.gen_pretimewin)

    def create_project(self, jnk_unused):
        #And load the new project window
        self.newprojectwin = fstimer.gui.newproject.NewProjectWin(self.set_projecttype,
                                                                  self.introwin)

    def set_projecttype(self, path, projectlist, combobox):
        '''creates a new project'''
        self.project_types = ['standard', 'handicap'] #Options for project types
        #First load in the project settings
        indx = combobox.get_active()
        if indx == 0:
            # Default settings
            fname = 'fstimer/data/fstimer_default_project.reg'
        else:
            importname = projectlist[indx]
            importpath = normpath(join(dirname(dirname(abspath(__file__))), importname))
            fname = os.path.join(importpath, importname+'.reg')
        with open(fname, 'r', encoding='utf-8') as fin:
            regdata = json.load(fin)
        #Assign all of the project settings
        self.fields = regdata['fields']
        self.fieldsdic = regdata['fieldsdic']
        self.clear_for_fam = regdata['clear_for_fam']
        self.divisions = regdata['divisions']
        self.projecttype = regdata['projecttype']
        self.numlaps = regdata['numlaps']
        '''Handles setting project type'''
        self.path = path
        self.projecttypewin = fstimer.gui.projecttype.ProjectTypeWin(self.project_types,
                                                                     self.projecttype,
                                                                     self.numlaps,
                                                                     self.back_to_new_project,
                                                                     self.define_fields,
                                                                     self.introwin)

    def define_fields(self, jnk_unused, rbs, check_button, numlapsbtn):
        '''Handled the definition of fields when creating a new project'''
        self.projecttypewin.hide()
        #First take care of the race settings from the previous window
        for b, btn in rbs.items():
            if btn.get_active():
                self.projecttype = self.project_types[b]
                break
        if check_button.get_active():
            self.numlaps = numlapsbtn.get_value_as_int()
        else:
            self.numlaps = 1
        #We will use self.fields and self.fieldsdic as already loaded, but add/remove Handicap field according projecttype.
        if self.projecttype == 'handicap':
            if 'Handicap' not in self.fields:
                self.fields.append('Handicap')
                self.fieldsdic['Handicap'] = {'type':'entrybox', 'max':20}
                self.clear_for_fam.append('Handicap')
        #And now generate the window.
        self.definefieldswin = fstimer.gui.definefields.DefineFieldsWin \
          (self.fields, self.fieldsdic, self.projecttype, self.back_to_projecttype,
           self.define_family_reset, self.introwin)

    def back_to_projecttype(self, jnk_unused):
        '''Goes back to new project window'''
        self.definefieldswin.hide()
        self.projecttypewin.show_all()

    def back_to_new_project(self, jnk_unused):
        '''Goes back to new project window'''
        self.projecttypewin.hide()
        self.newprojectwin.show_all()

    def define_family_reset(self, jnk_unused):
        '''Goes to family reset window'''
        self.definefieldswin.hide()
        self.familyresetwin = fstimer.gui.definefamilyreset.FamilyResetWin \
          (self.fields, self.clear_for_fam, self.back_to_define_fields,
           self.define_divisions, self.introwin)

    def back_to_define_fields(self, jnk_unused):
        '''Goes back to define fields window from the family reset one'''
        self.familyresetwin.hide()
        self.definefieldswin.show_all()

    def define_divisions(self, jnk_unused, btnlist):
        '''Defines default divisions and launched the division edition window'''
        self.clear_for_fam = []
        for (field, btn) in zip(self.fields, btnlist):
            if btn.get_active():
                self.clear_for_fam.append(field)
        self.familyresetwin.hide()
        self.divisionswin = fstimer.gui.definedivisions.DivisionsWin \
          (self.fields, self.fieldsdic, self.divisions, self.back_to_family_reset, self.store_new_project, self.introwin)

    def back_to_family_reset(self, jnk_unused):
        '''Goes back to family reset window, from the division edition one'''
        self.divisionswin.hide()
        self.familyresetwin.show_all()

    def store_new_project(self, jnk_unused):
        '''Stores a new project to file and goes to root window'''
        os.system('mkdir '+ self.path)
        regdata = {}
        regdata['projecttype'] = self.projecttype
        regdata['numlaps'] = self.numlaps
        regdata['fields'] = self.fields
        regdata['fieldsdic'] = self.fieldsdic
        regdata['clear_for_fam'] = self.clear_for_fam
        regdata['divisions'] = self.divisions
        with open(join(self.path, basename(self.path)+'.reg'), 'w', encoding='utf-8') as fout:
            json.dump(regdata, fout)
        md = MsgDialog(self.divisionswin, 'information', 'OK', 'Created!', 'Project '+basename(self.path)+' successfully created!')
        md.run()
        md.destroy()
        self.divisionswin.hide()
        self.introwin.hide()
        self.rootwin = fstimer.gui.root.RootWin(self.path,
                                                self.show_about,
                                                self.import_prereg,
                                                self.handle_preregistration,
                                                self.compreg_window,
                                                self.gen_pretimewin)

    def show_about(self, jnk_unused):
        '''Displays the about window'''
        fstimer.gui.about.AboutWin()

    def import_prereg(self, jnk_unused):
        '''import pre-registration from a csv'''
        self.importpreregwin = fstimer.gui.importprereg.ImportPreRegWin(self.path, self.fields, self.fieldsdic)

    def handle_preregistration(self, jnk_unused):
        '''handles preregistration'''
        self.preregistrationwin = fstimer.gui.preregister.PreRegistrationWin(self.path, self.set_registration_file, self.handle_registration)

    def set_registration_file(self, filename):
        '''set a preregistration file'''
        with open(filename, 'r', encoding='utf-8') as fin:
            self.prereg = json.load(fin)

    def handle_registration(self, regid):
        '''handles registration'''
        self.preregistrationwin.hide()
        self.regid = regid
        if not hasattr(self, 'prereg'):
            self.prereg = [] #No pre-registration was selected
        self.registrationwin = fstimer.gui.register.RegistrationWin(self.path, self.fields, self.fieldsdic, self.prereg, self.projecttype, self.save_registration)

    def save_registration(self):
        '''saves registration'''
        filename = os.path.join(self.path, basename(self.path)+'_registration_'+str(self.regid)+'.json')
        with open(filename, 'w', encoding='utf-8') as fout:
            json.dump(self.prereg, fout)
        return filename, True

    def compreg_window(self, jnk_unused):
        '''Merges registration files and create the timing dictionary.'''
        self.compilewin = fstimer.gui.compile.CompilationWin(self.path, self.merge_compreg)

    def merge_compreg(self, regfilelist):
        '''Merges the given registration files
           Loads all given json files and merge.
           Also creates a timing dictionary, which is a dictionary with IDs as keys.
           Finally, checks for errors'''
        if not regfilelist:
            # case of an empty list : nothing to be done
            return
        # Use labels to keep track of the status.
        self.compilewin.resetLabels()
        self.compilewin.setLabel(0, '<span color="blue">Combining registrations...</span>')
        # This will be a list of the merged registrations
        # each registration is a list of dictionaries
        self.regmerge = []
        for fname in regfilelist:
            with open(fname, 'r', encoding='utf-8') as fin:
                reglist = json.load(fin)
            self.regmerge.extend(reglist)
        # Now remove trivial dups
        self.reg_nodups0 = [dict(tupleized) for tupleized in set(
            tuple((field, item[field]) for field in self.fields) for item in self.regmerge)]
        # Get rid of entries that differ only by the ID. That is, items that were in the pre-reg and had no changes except an ID was assigned in one reg file.
        # we'll do this in O(n^2) time:-(
        self.reg_nodups = []
        for reg in self.reg_nodups0:
            if reg['ID']:
                self.reg_nodups.append(reg)
            else:
                # make sure there isn't an entry with everything else the same, but an ID
                dupcheck = False
                for i in range(len(self.reg_nodups0)):
                    dicttmp = self.reg_nodups0[i].copy()
                    if dicttmp['ID']:
                        #lets make sure we aren't a dup of this one
                        dicttmp['ID'] = ''
                        if reg == dicttmp:
                            dupcheck = True
                            break
                if not dupcheck:
                    self.reg_nodups.append(reg)
        # Now form the Timing dictionary, and check for errors.
        self.compilewin.setLabel(1, '<span color="blue">Checking for errors...</span>')
        # the timing dictionary. keys are IDs, values are registration dictionaries
        self.timedict = {}
        # the errors dictionary. keys are IDs, values are a list registration dictionaries with that ID
        self.errors = {}
        for reg in self.reg_nodups:
            # Any registration without an ID is left out of the timing dictionary
            if reg['ID']:
                # have we already added this ID to the timing dictionary?
                if reg['ID'] in self.timedict.keys():
                    # If so, then we need to first add to the list the reg that was already stored in timedict.
                    if reg['ID'] not in self.errors.keys():
                        self.errors[reg['ID']] = [self.timedict[reg['ID']]]
                    self.errors[reg['ID']].append(reg)
                else:
                    self.timedict[reg['ID']] = reg
        # If there are errors, we must correct them
        if self.errors:
            self.compilewin.setLabel(1, '<span color="blue">Checking for errors...</span> <span color="red">Errors found!</span>')
            # Now we make a dialog to deal with errors...
            self.comperrorswin = fstimer.gui.compileerrors.CompilationErrorsWin(self.path, self.compilewin, self.errors, self.fields, self.timedict, self.compreg_noerrors)
        else:
            # If no errors, continue on
            self.compreg_noerrors()

    def compreg_noerrors(self, errs=False):
        '''Writes registration and timing disctionnaries to the disk.
           This should be called when no errors remain'''
        if errs:
            self.compilewin.setLabel(1, '<span color="blue">Checking for errors... errors corrected.</span>')
        else:
            self.compilewin.setLabel(1, '<span color="blue">Checking for errors... no errors found!</span>')
        #Now save things
        with open(join(self.path, basename(self.path)+'_registration_compiled.json'), 'w', encoding='utf-8') as fout:
            json.dump(self.reg_nodups, fout)
        with open(join(self.path, basename(self.path)+'_timing_dict.json'), 'w', encoding='utf-8') as fout:
            json.dump(self.timedict, fout)
        regfn = join(self.path, basename(self.path) + '_registration_compiled.json')
        timefn = join(self.path, basename(self.path) + '_timing_dict.json')
        self.compilewin.setLabel(2, '<span color="blue">Successfully wrote files:\n' + \
                                 regfn + '\n' + timefn + '</span>')
        #And write the compiled registration to csv
        with open(join(self.path, basename(self.path)+'_registration.csv'), 'w', encoding='utf-8') as fout:
            dict_writer = csv.DictWriter(fout, self.fields)
            dict_writer.writer.writerow(self.fields)
            dict_writer.writerows(self.reg_nodups)
        return

    def gen_pretimewin(self, jnk_unused):
        '''Selects a timing dictionary to use'''
        self.timing = defaultdict(lambda: defaultdict(str))
        self.pretimewin = fstimer.gui.pretime.PreTimeWin(self.path, self.timing, self.gen_timewin)

    def gen_timewin(self, passid, timebtn):
        '''The actual timing'''
        self.passid = passid
        # we're done with pretiming
        self.pretimewin.hide()
        # We will store 'raw' data, lists of times and IDs.
        self.rawtimes = {'times':[], 'ids':[]}
        # create Timing window
        self.timewin = fstimer.gui.timing.TimingWin(self.path, self.rootwin, timebtn, self.rawtimes, self.timing, self.print_times, self.projecttype, self.numlaps, self.fields, self.fieldsdic, self.write_updated_timing)

    def write_updated_timing(self, reg, timedict):
        filename = os.path.join(self.path, os.path.basename(self.path)+'_registration_compiled.json')
        with open(filename, 'w', encoding='utf-8') as fout:
            json.dump(reg, fout)
        with open(join(self.path, basename(self.path)+'_timing_dict.json'), 'w', encoding='utf-8') as fout:
            json.dump(timedict, fout)
        with open(join(self.path, basename(self.path)+'_registration.csv'), 'w', encoding='utf-8') as fout:
            dict_writer = csv.DictWriter(fout, self.fields)
            dict_writer.writer.writerow(self.fields)
            dict_writer.writerows(reg)
        self.timing = timedict
        return filename

    def print_times(self, jnk_unused, use_csv):
        '''print times to a file'''
        # choose the right Printer Class
        if use_csv:
            if self.numlaps > 1:
                printer_class = fstimer.printcsvlaps.CSVPrinterLaps
            else:
                printer_class = fstimer.printcsv.CSVPrinter
        else:
            if self.numlaps > 1:
                printer_class = fstimer.printhtmllaps.HTMLPrinterLaps
            else:
                printer_class = fstimer.printhtml.HTMLPrinter
        # Figure out what the columns will be
        other_fields = set([field for div in self.divisions for field in div[1]
                            if field not in ['Age', 'Gender']])
        fields = ['Place', 'Time']
        if self.numlaps > 1:
            fields.append('Lap Times')
        fields.extend(['Name', 'Bib ID', 'Gender', 'Age'])
        fields.extend(list(other_fields))
        # instantiate the printer
        printer = printer_class(fields, [div[0] for div in self.divisions])
        # first build all results into strings
        scratchresults = printer.scratch_table_header()
        divresults = {div[0]:'\n'+printer.cat_table_header(div[0])
                      for div in self.divisions}
        for (tag, time) in self.get_sorted_results():
            scratchresults += printer.scratch_entry(tag, time, self.timing[tag])
            mydivs = self.get_division(self.timing[tag])
            for div in mydivs:
                divresults[div] += printer.cat_entry(tag, div, time, self.timing[tag])
        scratchresults += printer.scratch_table_footer()
        for div in divresults:
            divresults[div] += printer.cat_table_footer(div)
        # now save to files
        scratch_file = join(self.path,
                                    '_'.join([basename(self.path),
                                              self.timewin.timestr,
                                              'alltimes.' + printer.file_extension()]))
        with open(scratch_file, 'w', encoding='utf-8') as scratch_out:
            scratch_out.write(printer.header())
            scratch_out.write(scratchresults)
            scratch_out.write(printer.footer())
        div_file = join(self.path,
                                '_'.join([basename(self.path),
                                          self.timewin.timestr,
                                          'divtimes.' + printer.file_extension()]))
        with open(div_file, 'w', encoding='utf-8') as div_out:
            div_out.write(printer.header())
            for div in self.divisions:
                div_out.write(divresults[div[0]])
            div_out.write(printer.footer())
        # display user dialog that all was successful
        md = MsgDialog(self.timewin, 'information', 'OK', 'Saved!', "Results saved to " + printer.file_extension() + "!")
        md.run()
        md.destroy()

    def get_division(self, timingEntry):
        '''Get the divisions for a given timing entry'''
        try:
            age = int(timingEntry['Age'])
        except ValueError:
            age = ''
        mydivs = []
        # go through the divisions
        for div in self.divisions:
            # check all fields
            for field in div[1]:
                if field == 'Age':
                    if not age or age < div[1]['Age'][0] or age > div[1]['Age'][1]:
                        break
                else:
                    if timingEntry[field] != div[1][field]:
                        break
            else:
                mydivs.append(div[0])
        return mydivs

    def get_sync_times_and_ids(self):
        '''returns a list of ids and a list of timedeltas that are
           "synced", that is that have the same number of entries.
           Entries without a counterpart are dropped'''
        #Note that the newest entries are at the _start_ of the rawtimes lists
        offset = len(self.rawtimes['times']) - len(self.rawtimes['ids'])
        if offset < 0:
            adj_ids = self.rawtimes['ids'][-offset:]
            adj_times = list(self.rawtimes['times'])
        elif offset > 0:
            adj_ids = list(self.rawtimes['ids'])
            adj_times = self.rawtimes['times'][offset:]
        else:
            adj_ids = list(self.rawtimes['ids'])
            adj_times = list(self.rawtimes['times'])
        return adj_ids, adj_times

    def get_sorted_results(self):
        '''returns a sorted list of (id, result) items.
           The content of result depends on the race type'''
        # get raw times
        timeslist = zip(*self.get_sync_times_and_ids())
        #Handle blank times, and handicap correction
        # Handicap correction
        if self.projecttype == 'handicap':
            new_timeslist = []
            for tag, time in timeslist:
                if tag and time and tag != self.passid:
                    try:
                        new_timeslist.append((tag, time_diff(time,self.timing[tag]['Handicap'])))
                    except AttributeError:
                        #Either time or Handicap couldn't be converted to timedelta. It will be dropped.
                        pass
                #else: We just drop entries with blank tag, blank time, or the pass ID
            timeslist = list(new_timeslist) #replace
        else:
            #Drop times that are blank or have the passid
            timeslist = [(tag, time) for tag, time in timeslist if tag and time and tag != self.passid]
        # sort by time
        timeslist = sorted(timeslist, key=lambda entry: entry[1])
        # single lap case
        if self.numlaps == 1:
            return timeslist
        else:
            # multi laps - groups times by tag
            # Each value of laptimesdic is a list, sorted in order from
            # fastest time (1st lap) to longest time (last lap).
            laptimesdic = defaultdict(list)
            for (tag, time) in timeslist:
                laptimesdic[tag].append(time)
            # compute the lap times.
            laptimesdic2 = defaultdict(list)
            for tag in laptimesdic:
                # First put the total race time
                if len(laptimesdic[tag]) == self.numlaps:
                    laptimesdic2[tag] = [laptimesdic[tag][-1]]
                else:
                    laptimesdic2[tag] = ['<>']
                # And now the first lap
                laptimesdic2[tag].append(laptimesdic[tag][0])
                # And now the subsequent laps
                laptimesdic2[tag].extend([time_diff(laptimesdic[tag][ii+1],laptimesdic[tag][ii]) for ii in range(len(laptimesdic[tag])-1)])
            return sorted(laptimesdic2.items(), key=lambda entry: entry[1][0])
