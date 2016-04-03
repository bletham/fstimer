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
import fstimer.gui.definedivisions
import fstimer.gui.printfields
import fstimer.gui.definerankings
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
        try:
            self.rankings = regdata['rankings']
        except KeyError:
            # old project, with no rankings, rankings is thus default one
            self.rankings = {'Overall': 'Time'}
            for div in self.divisions:
                self.rankings[div[0]] = 'Time'
        try:
            self.printfields = regdata['printfields']
        except KeyError:
            # fill with default
            self.printfields = {'Time': '{Time_str}'}
            for field in ['ID', 'Age', 'Gender']:
                self.printfields[field] = '{' + field + '}'
            if 'Name' not in self.fields:
                self.printfields['Name'] = "{First name} + ' ' + {Last name}"
            
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
        self.divisions = regdata['divisions']
        self.projecttype = regdata['projecttype']
        self.numlaps = regdata['numlaps']
        try:
            self.rankings = regdata['rankings']
        except KeyError:
            # old project, with no rankings, rankings is thus default one
            self.rankings = {'Overall': 'Time'}
            for div in self.divisions:
                self.rankings[div[0]] = 'Time'
        try:
            self.printfields = regdata['printfields']
        except KeyError:
            self.printfields = {}
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
        #And now generate the window.
        self.definefieldswin = fstimer.gui.definefields.DefineFieldsWin \
          (self.fields, self.fieldsdic, self.projecttype, self.back_to_projecttype,
           self.define_divisions, self.introwin)

    def back_to_projecttype(self, jnk_unused):
        '''Goes back to new project window'''
        self.definefieldswin.hide()
        self.projecttypewin.show_all()

    def back_to_new_project(self, jnk_unused):
        '''Goes back to new project window'''
        self.projecttypewin.hide()
        self.newprojectwin.show_all()
    
    def define_divisions(self, jnk_unused):
        '''Defines default divisions and launched the division edition window'''
        self.definefieldswin.hide()
        self.divisionswin = fstimer.gui.definedivisions.DivisionsWin \
          (self.fields, self.fieldsdic, self.divisions, self.back_to_fields, self.print_fields, self.introwin)

    def back_to_fields(self, jnk_unused):
        '''Goes back to family reset window, from the division edition one'''
        self.divisionswin.hide()
        self.definefieldswin.show_all()
        
    def print_fields(self, jnk_unused):
        '''Launch print fields window'''
        # First filter the current self.printfields to only include ones that use fields
        # from self.fields.
        bad_fields = []
        for field, text in self.printfields.items():
            if not (field in self.fields or field in ['Time', 'Pace']):
                vars_ = re.findall("\{[^}]+\}", text)
                for var in vars_:
                    name = var[1:-1]
                    if not (name in self.fields or name == 'Time'):
                        bad_fields.append(field)
        for field in bad_fields:
            self.printfields.pop(field)
        # Now launch the window
        self.divisionswin.hide()
        self.printfieldswin = fstimer.gui.printfields.PrintFieldsWin(
            self.fields, self.printfields, self.back_to_divisions, self.define_rankings, self.introwin)
    
    def back_to_divisions(self, jnk_unused, btnlist, btn_time, btn_pace, entry_pace, printfields_m):
        '''Goes back to define fields window from the print fields'''
        res = self.set_printfields(btnlist, btn_time, btn_pace, entry_pace, printfields_m)
        if not res:
            return
        #else
        self.printfieldswin.hide()
        self.divisionswin.show_all()
    
    def set_printfields(self, btnlist, btn_time, btn_pace, entry_pace, printfields_m):
        '''Update self.printfields'''
        # First check it is valid.
        if btn_pace.get_active():
            try:
                d = float(entry_pace.get_text())
            except ValueError:
                md = MsgDialog(self.printfieldswin, 'error', 'OK', 'Error!', 'Distance must be a number.')
                md.run()
                md.destroy()
                return False
        # It will be valid. Let's continue.
        self.printfields = {}  # re-set
        # Start with the registration fields
        for field, btn in zip(self.fields, btnlist):
            if btn.get_active():
                self.printfields[field] = '{' + field + '}'
        # Then timing button and pace button
        if btn_time.get_active():
            self.printfields['Time'] = '{Time_str}'
        if btn_pace.get_active():
            self.printfields['Pace'] = '{Time} / 60 / ' + entry_pace.get_text()
        # Finally custom fields
        for field in printfields_m:
            if field not in self.fields and field not in ['Time', 'Pace']:
                self.printfields[field] = str(printfields_m[field])
        if len(self.printfields) == 0:
            md = MsgDialog(self.printfieldswin, 'error', 'OK', 'Error!', 'Must include at least one field.')
            md.run()
            md.destroy()
            return False
        return True
    
    def define_rankings(self, jnk_unused, btnlist, btn_time, btn_pace, entry_pace, printfields_m):
        '''Goes to the define rankings window'''
        # Store away the printfields information.
        res = self.set_printfields(btnlist, btn_time, btn_pace, entry_pace, printfields_m)
        if not res:
            return
        # else move on.
        # Edit the current self.rankings to make sure its keys match the divisions in div.
        old_divs = list(self.rankings.keys())
        old_divs.remove('Overall')
        for div, descr in self.divisions:
            if div not in self.rankings:
                self.rankings[div] = self.rankings['Overall']
            else:
                old_divs.remove(div)
        # Get rid of any removed divs
        for div in old_divs:
            self.rankings.pop(div)
        # Now we're ready.
        self.printfieldswin.hide()
        self.rankingswin = fstimer.gui.definerankings.RankingsWin(
            self.rankings, self.divisions, self.printfields, self.back_to_printfields, self.store_new_project, self.introwin)

    def back_to_printfields(self, jnk_unused):
        '''Goes back to define fields window from the family reset one'''
        self.rankingswin.hide()
        self.printfieldswin.show_all()

    def store_new_project(self, jnk_unused):
        '''Stores a new project to file and goes to root window'''
        os.system('mkdir '+ self.path)
        regdata = {}
        regdata['projecttype'] = self.projecttype
        regdata['numlaps'] = self.numlaps
        regdata['fields'] = self.fields
        regdata['fieldsdic'] = self.fieldsdic
        regdata['printfields'] = self.printfields
        regdata['divisions'] = self.divisions
        regdata['rankings'] = self.rankings
        with open(join(self.path, basename(self.path)+'.reg'), 'w', encoding='utf-8') as fout:
            json.dump(regdata, fout)
        md = MsgDialog(self.divisionswin, 'information', 'OK', 'Created!', 'Project '+basename(self.path)+' successfully created!')
        md.run()
        md.destroy()
        self.rankingswin.hide()
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
        '''print times to files'''
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
        # Figure out what the columns will be.
        cols = []
        # Prefer next time, and then pace, if they are in the printfields
        for field in ['Time', 'Pace']:
            if field in self.printfields:
                cols.append(field)
        if self.numlaps > 1 and 'Time' in self.printfields:
            cols.append('Lap Times')
        # Then add in the calculated fields, and then registration fields
        regfields = []
        for field in self.printfields:
            if field in self.fields:
                regfields.append(field)
            elif field in ['Time', 'Pace']:
                pass  # already covered
            else:
                cols.append(field)  # A computed field
        cols.extend(regfields)
        # Prepare functions for computing each column
        col_fns = []
        for col in cols:
            if col == 'Lap Times':
                text = 'lap_time'
            else:
                text = self.printfields[col]
                # Sub {Time} and {Time_str}
                text = text.replace('{Time_str}', 'time')
                text = text.replace('{Time}', 'time.total_seconds()')
                # Age
                text = text.replace('{Age}', "int(userdata['Age'])")
                # ID
                text = text.replace('{ID}', "tag")
                # And the other registration fields
                for field in self.fields:
                    if field not in ['Age', 'ID']:
                        text = text.replace('{' + field + '}', "userdata['{}']".format(field))
            col_fns.append(text)
        # Get the list of different things we will rank by
        ranking_keys = set(self.rankings.values())
        # instantiate the printer
        printer = printer_class(cols, [div[0] for div in self.divisions])
        # Build the results
        scratchresults = printer.scratch_table_header()
        divresults = {div[0]:'\n'+printer.cat_table_header(div[0])
                      for div in self.divisions}
        # Do the ranking for each ranking key
        ranked_results = {}
        for ranking_key in ranking_keys:
            rank_indx = cols.index(ranking_key)
            ranked_results = self.get_sorted_results(rank_indx, col_fns)
            for tag, row in ranked_results:
                # Add this to the appropriate results
                if self.rankings['Overall'] == ranking_key:
                    scratchresults += printer.scratch_entry(row)
                mydivs = self.get_divisions(tag)
                for div in mydivs:
                    if self.ranking[div] == ranking_key:
                        divresults[div] += printer.cat_entry(div, row)
        scratchresults += printer.scratch_table_footer()
        for div in divresults:
            divresults[div] += printer.cat_table_footer(div)
        # now save to files
        scratch_file = os.path.join(self.path,
                                    '_'.join([self.projectname,
                                                self.timewin.timestr,
                                                'alltimes.' + printer.file_extension()]))
        with open(scratch_file, 'w') as scratch_out:
            scratch_out.write(printer.header())
            scratch_out.write(scratchresults)
            scratch_out.write(printer.footer())
        div_file = os.path.join(self.path,
                                '_'.join([self.projectname,
                                            self.timewin.timestr,
                                            'divtimes.' + printer.file_extension()]))
        with open(div_file, 'w') as div_out:
            div_out.write(printer.header())
            for div in self.divisions:
                div_out.write(divresults[div[0]])
            div_out.write(printer.footer())
        # display user dialog that all was successful
        md = MsgDialog(self.timewin, 'information', 'OK', 'Success!', "Results saved to " + printer.file_extension() + "!")
        md.run()
        md.destroy()

    def get_divisions(self, tag):
        '''Get the divisions for a given timing entry'''
        try:
            age = int(self.timing[tag]['Age'])
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
                    if self.timing[tag][field] != div[1][field]:
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

    def get_sorted_results(self, rank_indx, col_fns):
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
        # Compute lap times, if a lap race
        if self.numlaps > 1:
            # multi laps - groups times by tag
            # Each value of laptimesdic is a list, sorted in order from
            # fastest time (1st lap) to longest time (last lap).
            laptimesdic = defaultdict(list)
            for (tag, time) in sorted(timeslist, key=lambda x:x[1]):
                laptimesdic[tag].append(time)
            # compute the lap times.
            lap_times = {}
            total_times = {}
            for tag in laptimesdic:
                # First put the total race time
                if len(laptimesdic[tag]) == self.numlaps:
                    total_times[tag] = laptimesdic[tag][-1]
                else:
                    total_times[tag] = '<>'
                # And the first lap
                lap_times[tag] = ['1 - ' + laptimesdic[tag][0]]
                # And now the subsequent laps
                for ii in range(len(laptimesdic[tag])-1):
                    lap_times[tag].append(str(ii+2) + ' - ' + time_diff(laptimesdic[tag][ii+1],laptimesdic[tag][ii]))
            # Now correct timeslist to have the new total times
            timeslist = list(total_times.items())
        else:
            lap_times = defaultdict(int)
        # Compute each results row
        result_rows = []
        for tag, time in timeslist:
            row = []
            lap_time = lap_times[tag]
            userdata = self.timing[tag]
            for i, col_fn in enumerate(col_fns):
                try:
                    row.append(str(eval(col_fn)))
                except (SyntaxError, TypeError, AttributeError, ValueError):
                    if i == rank_indx:
                        row.append('<>')  # To push null values to the bottom
                    else:
                        row.append('')
            result_rows.append((tag, row))
        # sort by key
        result_rows = sorted(result_rows, key=lambda x: x[1][rank_indx])
        # remove duplicate entries: If a tag has multiple entries, keep only the most highly ranked.
        taglist = set()
        result_rows_dedup = []
        for tag, row in result_rows:
            if tag in taglist:
                pass  # drop it
            else:
                taglist.add(tag)
                result_rows_dedup.append((tag, row))
        return result_rows_dedup
