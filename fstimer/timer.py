#!/usr/bin/env python3

#fsTimer - free, open source software for race timing.
#Copyright 2012-17 Ben Letham

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

import logging
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
from fstimer.printer.formatter import print_startsheets
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
        projectname = projectlist[combobox.get_active()]
        self.path = normpath(join(dirname(dirname(abspath(__file__))), projectname))
        #self.path is now _absolute_, it is not project name.
        with open(join(self.path, projectname + '.reg'), 'r', encoding='utf-8') as fin:
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
            self.variablelaps = regdata['variablelaps']
        except KeyError:
            self.variablelaps = False
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
            self.printfields = {'Time': '{time}'}
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
                                                self.gen_pretimewin,
                                                self.define_divisions)

    def create_project(self, jnk_unused):
        #And load the new project window
        self.newprojectwin = fstimer.gui.newproject.NewProjectWin(self.set_projecttype,
                                                                  self.introwin)

    def set_projecttype(self, projectname, projectlist, combobox):
        '''creates a new project'''
        self.project_types = ['standard', 'handicap'] #Options for project types
        #First load in the project settings
        indx = combobox.get_active()
        if indx == 0:
            # Default settings
            fname = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'data/fstimer_default_project.reg'))
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
            self.variablelaps = regdata['variablelaps']
        except KeyError:
            # old project, for backwards compatibility
            self.variablelaps = False
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
        self.path = normpath(join(dirname(dirname(abspath(__file__))), projectname))
        self.projecttypewin = fstimer.gui.projecttype.ProjectTypeWin(self.project_types,
                                                                     self.projecttype,
                                                                     self.numlaps,
                                                                     self.variablelaps,
                                                                     self.back_to_new_project,
                                                                     self.define_fields,
                                                                     self.introwin)

    def define_fields(self, jnk_unused, rbs, check_button, check_button2, numlapsbtn):
        '''Handled the definition of fields when creating a new project'''
        self.projecttypewin.hide()
        #First take care of the race settings from the previous window
        for b, btn in rbs.items():
            if btn.get_active():
                self.projecttype = self.project_types[b]
                break
        if check_button.get_active():
            self.numlaps = numlapsbtn.get_value_as_int()
            if check_button2.get_active():
                self.variablelaps = True
        else:
            self.numlaps = 1
            self.variablelaps = False
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
    
    def define_divisions(self, jnk_unused, edit=False):
        '''Defines default divisions and launched the division edition window'''
        # First edit the current divisions to use only available fields
        divs = []
        for div, fields_dict in self.divisions:
            keep_div = True
            for field in fields_dict:
                if field not in self.fields:
                    keep_div = False
                    break
            if keep_div:
                divs.append([div, fields_dict])
        # replace
        self.divisions = list(divs)
        # continue
        if edit:
            parent_win = self.rootwin
        else:
            self.definefieldswin.hide()
            parent_win = self.introwin
        self.divisionswin = fstimer.gui.definedivisions.DivisionsWin \
          (self.fields, self.fieldsdic, self.divisions, self.back_to_fields, self.print_fields, parent_win, edit)

    def back_to_fields(self, jnk_unused):
        '''Goes back to family reset window, from the division edition one'''
        self.divisionswin.hide()
        self.definefieldswin.show_all()
        
    def print_fields(self, jnk_unused, edit):
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
                        break
        for field in bad_fields:
            self.printfields.pop(field)
        # Now launch the window
        parent_win = self.rootwin if edit else self.introwin
        self.divisionswin.hide()
        self.printfieldswin = fstimer.gui.printfields.PrintFieldsWin(
            self.fields, self.printfields, self.back_to_divisions, self.define_rankings, parent_win, edit)
    
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
                md = MsgDialog(self.printfieldswin, 'error', ['ok'], 'Error!', 'Distance must be a number.')
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
            self.printfields['Time'] = '{Time}'
        if btn_pace.get_active():
            self.printfields['Pace'] = '{Time}/' + entry_pace.get_text()
        # Finally custom fields
        for field in printfields_m:
            if field not in self.fields and field not in ['Time', 'Pace']:
                self.printfields[field] = str(printfields_m[field])
        if len(self.printfields) == 0:
            md = MsgDialog(self.printfieldswin, 'error', ['ok'], 'Error!', 'Must include at least one field.')
            md.run()
            md.destroy()
            return False
        return True
    
    def define_rankings(self, jnk_unused, btnlist, btn_time, btn_pace, entry_pace, printfields_m, edit):
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
        # Also change any rankings that are set to fields that no longer exist
        # First for overall
        if self.rankings['Overall'] not in self.printfields:
            # Set to the first item by default then
            self.rankings['Overall'] = list(self.printfields.keys())[0]
        # Now check the others
        for ranking in self.rankings:
            if self.rankings[ranking] not in self.printfields:
                self.rankings[ranking] = self.rankings['Overall']
        # Now we're ready.
        parent_win = self.rootwin if edit else self.introwin
        self.printfieldswin.hide()
        self.rankingswin = fstimer.gui.definerankings.RankingsWin(
            self.rankings, self.divisions, self.printfields, self.back_to_printfields, self.store_new_project, parent_win, edit)

    def back_to_printfields(self, jnk_unused):
        '''Goes back to define fields window from the family reset one'''
        self.rankingswin.hide()
        self.printfieldswin.show_all()

    def store_new_project(self, jnk_unused, edit):
        '''Stores a new project to file and goes to root window'''
        logger = logging.getLogger('fstimer')
        logger.debug(self.path)
        if not edit:
            os.system('mkdir '+ self.path)
        regdata = {}
        regdata['projecttype'] = self.projecttype
        regdata['numlaps'] = self.numlaps
        regdata['variablelaps'] = self.variablelaps
        regdata['fields'] = self.fields
        regdata['fieldsdic'] = self.fieldsdic
        regdata['printfields'] = self.printfields
        regdata['divisions'] = self.divisions
        regdata['rankings'] = self.rankings
        logger.debug(regdata)
        # Check if project directory exists
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        with open(join(self.path, basename(self.path)+'.reg'), 'w', encoding='utf-8') as fout:
            json.dump(regdata, fout)
        if edit:
            md = MsgDialog(self.rankingswin, 'information', ['ok'], 'Edited!', 'Project '+basename(self.path)+' successfully edited!')
        else:
            md = MsgDialog(self.rankingswin, 'information', ['ok'], 'Created!', 'Project '+basename(self.path)+' successfully created!')
        md.run()
        md.destroy()
        self.rankingswin.hide()
        if not edit:
            self.introwin.hide()
            self.rootwin = fstimer.gui.root.RootWin(self.path,
                                                    self.show_about,
                                                    self.import_prereg,
                                                    self.handle_preregistration,
                                                    self.compreg_window,
                                                    self.gen_pretimewin,
                                                    self.define_divisions)

    def show_about(self, jnk_unused, parent):
        '''Displays the about window'''
        fstimer.gui.about.AboutWin(parent)

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
        regfn = join(self.path, basename(self.path) + '_registration_compiled.json')
        timefn = join(self.path, basename(self.path) + '_timing_dict.json')
        with open(regfn, 'w', encoding='utf-8') as fout:
            json.dump(self.reg_nodups, fout)
        with open(timefn, 'w', encoding='utf-8') as fout:
            json.dump(self.timedict, fout)
        print_startsheets(self, use_csv=False)
        self.compilewin.setLabel(
            2,
            '<span color="blue">Successfully wrote files:\n' + regfn + '\n' +
            timefn + '\n\nStart sheets written to html.\n </span>')
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
        self.timewin = fstimer.gui.timing.TimingWin(self, timebtn)

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
