#!/usr/bin/env python

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

'''Main class of hte fsTimer package'''

import pygtk
pygtk.require('2.0')
import gtk
import os, json, csv, re, datetime
import fstimer.gui.intro
import fstimer.gui.newproject
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
from collections import defaultdict

class PyTimer(object):
    '''main class of fsTimer'''

    def __init__(self):
        '''constructor method. Displays top level window'''
        self.introwin = fstimer.gui.intro.IntroWin(self.load_project,
                                                   self.create_project)
        self.prereg = []

    def load_project(self, jnk_unused, combobox, projectlist):
        '''Loads the registration settings of a project, and go back to rootwin'''
        self.path = projectlist[combobox.get_active()]
        with open(os.sep.join([self.path, self.path+'.reg']), 'rb') as fin:
            regdata = json.load(fin)
        self.fields = regdata['fields']
        self.fieldsdic = regdata['fieldsdic']
        self.clear_for_fam = regdata['clear_for_fam']
        self.divisions = regdata['divisions']
        self.introwin.hide()
        self.rootwin = fstimer.gui.root.RootWin(self.path,
                                                self.show_about,
                                                self.import_prereg,
                                                self.handle_preregistration,
                                                self.compreg_window,
                                                self.gen_pretimewin)

    def create_project(self, jnk_unused):
        '''creates a new project'''
        self.newprojectwin = fstimer.gui.newproject.NewProjectWin(self.define_fields,
                                                                  self.introwin)

    def define_fields(self, path):
        '''Handled the definition of fields when creating a new project'''
        #this is really just fsTimer.fieldsdic.keys(), but is important because it defines the order in which fields show up on the registration screen
        self.fields = ['Last name', 'First name', 'ID', 'Age', 'Gender',
                       'Address', 'Email', 'Telephone', 'Contact for future races',
                       'How did you hear about race']
        self.path = path
        self.fieldsdic = {}
        self.fieldsdic['Last name'] = {'type':'entrybox', 'max':30}
        self.fieldsdic['First name'] = {'type':'entrybox', 'max':30}
        self.fieldsdic['ID'] = {'type':'entrybox', 'max':6}
        self.fieldsdic['Age'] = {'type':'entrybox', 'max':3}
        self.fieldsdic['Gender'] = {'type':'combobox', 'options':['male', 'female']}
        self.fieldsdic['Address'] = {'type':'entrybox', 'max':90}
        self.fieldsdic['Email'] = {'type':'entrybox', 'max':40}
        self.fieldsdic['Telephone'] = {'type':'entrybox', 'max':20}
        self.fieldsdic['Contact for future races'] = {'type':'combobox', 'options':['yes', 'no']}
        self.fieldsdic['How did you hear about race'] = {'type':'entrybox', 'max':40}
        self.definefieldswin = fstimer.gui.definefields.DefineFieldsWin \
          (self.fields, self.fieldsdic, self.back_to_new_project,
           self.define_family_reset, self.introwin)

    def back_to_new_project(self, jnk_unused):
        '''Goes back to new project window'''
        self.definefieldswin.hide()
        self.newprojectwin.show_all()

    def define_family_reset(self, jnk_unused):
        '''Goes to family reset window'''
        self.definefieldswin.hide()
        self.familyresetwin = fstimer.gui.definefamilyreset.FamilyResetWin \
          (self.fields, self.back_to_define_fields, self.define_divisions, self.introwin)

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
        #Here we specify the default divisions.
        self.divisions = []
        self.divisions.append(('Female, ages 10 and under', {'Gender':'female', 'Age':(0, 10)}))
        self.divisions.append(('Male, ages 10 and under', {'Gender':'male', 'Age':(0, 10)}))
        for i in range(13):
            for gender in ['Female', 'Male']:
                minage = 10+i*5
                maxage = 10+i*5+4
                divname = gender+', ages '+str(minage)+'-'+str(maxage)
                self.divisions.append((divname, {'Gender':gender.lower(), 'Age':(minage, maxage)}))
        self.divisions.append(('Female, ages 80 and up', {'Gender':'female', 'Age':(80, 120)}))
        self.divisions.append(('Male, ages 80 and up', {'Gender':'male', 'Age':(80, 120)}))
        self.divisionswin = fstimer.gui.definedivisions.DivisionsWin \
          (self.fields, self.fieldsdic, self.divisions, self.back_to_define_fields2, self.store_new_project, self.introwin)

    def back_to_define_fields2(self, jnk_unused):
        '''Goes back to define fields window, from the division edition one'''
        self.divisionswin.hide()
        self.definefieldswin.show_all()

    def store_new_project(self, jnk_unused):
        '''Stores a new project to file and goes back to root window'''
        os.system('mkdir '+self.path)
        regdata = {}
        regdata['fields'] = self.fields
        regdata['fieldsdic'] = self.fieldsdic
        regdata['clear_for_fam'] = self.clear_for_fam
        regdata['divisions'] = self.divisions
        with open(os.sep.join([self.path, self.path+'.reg']), 'wb') as fout:
            json.dump(regdata, fout)
        md = gtk.MessageDialog(self.divisionswin, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, 'Project '+self.path+' successfully created!')
        md.run()
        md.destroy()
        self.divisionswin.hide()
        self.introwin.hide()
        self.rootwin = fstimer.gui.root.RootWin('fsTimer - '+self.path,
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
        self.importpreregwin = fstimer.gui.importprereg.ImportPreRegWin(os.getcwd(), self.path, self.fields, self.fieldsdic)

    def handle_preregistration(self, jnk_unused):
        '''handles preregistration'''
        self.preregistrationwin = fstimer.gui.preregister.PreRegistrationWin(os.getcwd(), self.path, self.set_registration_file, self.handle_registration)

    def set_registration_file(self, filename):
        '''set a preregistration file'''
        with open(filename, 'rb') as fin:
          self.prereg = json.load(fin)

    def handle_registration(self, jnk_unused, regid_btn):
        '''handles registration'''
        self.regid = regid_btn.get_value_as_int()
        self.preregistrationwin.hide()
        self.registrationwin = fstimer.gui.register.RegistrationWin(self.path, self.fields, self.fieldsdic, self.prereg, self.clear_for_fam, self.save_registration)

    def save_registration(self):
        '''saves registration'''
        filename = os.sep.join([self.path, self.path+'_registration_'+str(self.regid)+'.json'])
        with open(filename, 'wb') as fout:
            json.dump(self.prereg, fout)
        return filename

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
            with open(fname, 'rb') as fin:
                reglist = json.load(fin)
            self.regmerge.extend(reglist)
        # Now remove trivial dups
        self.reg_nodups0 = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in self.regmerge)]
        # Get rid of entries that differ only by the ID. That is, items that were in the pre-reg and had no changes except an ID was assigned in one reg file.
        # we'll do this in O(n^2) time:-(
        self.reg_nodups = []
        for reg in self.reg_nodups0:
            if reg['ID']:
                self.reg_nodups.append(reg)
            else:
                # make sure there isn't an entry with everything else the same, but an ID
                dupcheck = 0
                for i in range(len(self.reg_nodups0)):
                    dicttmp = self.reg_nodups0[i].copy()
                    if dicttmp['ID']:
                        #lets make sure we aren't a dup of this one
                        dicttmp['ID'] = ''
                        if reg == dicttmp:
                            dupcheck = 1
                if dupcheck == 0:
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
                    # If not, then we need to first add to the list the reg that was already stored in timedict.
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
        with open(os.sep.join([self.path, self.path+'_registration_compiled.json']), 'wb') as fout:
            json.dump(self.reg_nodups, fout)
        with open(os.sep.join([self.path, self.path+'_timing_dict.json']), 'wb') as fout:
            json.dump(self.timedict, fout)
        regfn = os.sep.join([self.path, self.path + '_registration_compiled.json'])
        timefn = os.sep.join([self.path, self.path + '_timing_dict.json'])
        self.compilewin.setLabel(2, '<span color="blue">Successfully wrote files:\n' + \
                                 regfn + '\n' + timefn + '</span>')
        #And write the compiled registration to csv
        with open(os.sep.join([self.path, self.path+'_registration.csv']), 'wb') as fout:
            dict_writer = csv.DictWriter(fout, self.fields)
            dict_writer.writer.writerow(self.fields)
            dict_writer.writerows(self.reg_nodups)
        return

    def gen_pretimewin(self, jnk_unused):
        '''Selects a timing dictionary to use'''
        self.timing = defaultdict(lambda: defaultdict(str))
        self.pretimewin = fstimer.gui.pretime.PreTimeWin(self.path, self.timing, self.gen_timewin)

    def gen_timewin(self, junkid, timebtn, strpzeros, numlaps):
        '''The actual timing'''
        self.junkid = junkid
        timebtn = timebtn
        strpzeros = strpzeros
        self.numlaps = numlaps
        # we're done with pretiming
        self.pretimewin.hide()
        # We will store 'raw' data, lists of times and IDs.
        self.rawtimes = {'times':[], 'ids':[]}
        # create Timing window
        self.timewin = fstimer.gui.timing.TimingWin(self.path, self.rootwin, timebtn, strpzeros, self.rawtimes, self.timing, self.print_times)

    def print_times(self, jnk_unused, use_csv):
        '''print times to a file'''
        if use_csv:
            if self.numlaps > 1:
                self.print_times_csv_laps()
            else:
                self.print_times_csv()
        else:
            if self.numlaps > 1:
                self.print_times_html_laps()
            else:
                self.print_times_html()

    def print_times_html(self):
        '''Prints the current time results to a nice html table.
           the entire table is reformed every time,
           so this may get slow for a large number of racers ?'''
        # Figure out what the columns will be, other than id/age/gender
        colnames = [field for div in self.divisions for field in div[1]]
        colnames = set(colnames)
        if 'Age' in colnames:
            colnames.remove('Age')
        if 'Gender' in colnames:
            colnames.remove('Gender')
        # We will only add these columns if they aren't too long (to overflow the page). We allow up to a total of 20 characters.
        if sum([len(colname) for colname in colnames]) > 20:
            colnames = []
        # Now begin to construct strings
        # The first string will be all of the head information for the html page, including the css styles.
        htmlhead = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <style type="text/css">
        #tab
        {
              font-family: Sans-Serif;
              font-size: 14px;
              margin: 20px;
              width: 650px;
              text-align: left;
        }
        #tab th
        {
              font-size: 15px;
              font-weight: bold;
              padding: 10px 8px;
              border-bottom: 2px solid gray;
        }
        #tab td
        {
              border-bottom: 1px solid #ccc;
              padding: 6px 8px;
        }
        #footer{ margin-top: 20px; margin-left: 20px; font: 10px sans-serif;}
        </style>
        </head>
        <body>\n"""
        # the second string will be the beginning of a table.
        tablehead = """<table id="tab">
        <thead>
        <tr>
        <th scope="col">Place</th>
        <th scope="col">Time</th>
        <th scope="col">Name</th>
        <th scope="col">Bib ID</th>
        <th scope="col">Gender</th>
        <th scope="col">Age</th>"""
        # And now the extra column names
        for colname in colnames:
            tablehead += '<th scope="col">'+colname+'</th>'
        # Now continue on
        tablehead += """</tr></thead><tbody>\n"""
        tablefoot = '</tbody></table>'
        htmlfoot = '<div id="footer">Race timing with fsTimer - free, open source software for race timing. http://fstimer.org</div></body></html>'
        # First we prepare the fullresults string.
        fullresults = htmlhead+tablehead
        # and each of the division results
        divresults = ['<span style="font-size:22px">'+str(div[0])+'</span>\n'+tablehead for div in self.divisions]
        allplace = 1
        divplace = [1 for div in self.divisions]
        # go through the data from fastest time to slowest
        if self.timewin.offset >= 0:
            adj_ids = ['' for i_unused in range(self.timewin.offset)]
            adj_ids.extend(self.rawtimes['ids'])
            adj_times = list(self.rawtimes['times'])
        elif self.timewin.offset < 0:
            adj_times = ['' for i_unused in range(-self.timewin.offset)]
            adj_times.extend(self.rawtimes['times'])
            adj_ids = list(self.rawtimes['ids'])
        printed_ids = set([self.junkid]) #keep track of the ones we've already seen
        for (tag, time) in sorted(zip(adj_ids, adj_times), key=lambda entry: entry[1]):
            if tag and time and tag not in printed_ids:
                printed_ids.add(tag)
                age = self.timing[tag]['Age']
                gen = self.timing[tag]['Gender']
                # Our table entry will be the same for both full results and divisionals, except for the place.
                tableentry = '</td><td>'+time+'</td><td>'+self.timing[tag]['First name']+' '+self.timing[tag]['Last name']+'</td><td>'+tag+'</td><td>'+gen+'</td><td>'+age+'</td>'
                # And now add in the extra columns
                for colname in colnames:
                    tableentry += '<td>'+self.timing[tag][colname]+'</td>'
                tableentry += '</tr>\n'
                #And add to full results
                fullresults += '<tr><td>'+str(allplace)+tableentry
                allplace += 1
                # and the appropriate divisional result
                try:
                    age = int(age)
                except ValueError:
                    age = ''
                # Now we go through the divisions
                for (divindx, div) in enumerate(self.divisions):
                    # First check age.
                    divcheck = True
                    for field in div[1]:
                        if field == 'Age':
                            if not age:
                                divcheck = False
                            elif age < div[1]['Age'][0] or age > div[1]['Age'][1]:
                                divcheck = False
                        else:
                            if self.timing[tag][field] != div[1][field]:
                              divcheck = False
                    #Now add this result to the div results, if it satisfied the requirements
                    if divcheck:
                        divresults[divindx] += '<tr><td>'+str(divplace[divindx])+tableentry
                        divplace[divindx] += 1
            # And write to file.
            with open(os.sep.join([self.path, self.path+'_'+self.timewin.timestr+'_alltimes.html']), 'w') as fout:
                fout.write(fullresults+tablefoot+htmlfoot)
            with open(os.sep.join([self.path, self.path+'_'+self.timewin.timestr+'_divtimes.html']), 'w') as fout:
                fout.write(htmlhead)
                for (divindx, divstr) in enumerate(divresults):
                    if divplace[divindx] > 1:
                        fout.write(divstr+tablefoot)
                fout.write(htmlfoot)
        md = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, "Results saved to html!")
        md.run()
        md.destroy()

    def print_times_csv(self):
        '''Prints the current time results to a csv file.
           the entire table is reformed every time,
           so this may get slow for a large number of racers ?'''
        # Figure out what the columns will be, other than id/age/gender
        colnames = [field for div in self.divisions for field in div[1]]
        colnames = set(colnames)
        if 'Age' in colnames:
            colnames.remove('Age')
        if 'Gender' in colnames:
            colnames.remove('Gender')
        # Create the header string
        tablehead = 'Place,Time,Name,Bib ID,Gender,Age'
        for colname in colnames:
            tablehead += ','+colname
        tablehead += '\n'
        # Keep track of the places
        allplace = 1
        divplace = [1 for div in self.divisions]
        divresults = ['\n'+div[0]+'\n'+tablehead for div in self.divisions]
        # go through the data from fastest time to slowest
        if self.timewin.offset >= 0:
            adj_ids = ['' for i in range(self.timewin.offset)]
            adj_ids.extend(self.rawtimes['ids'])
            adj_times = list(self.rawtimes['times'])
        elif self.timewin.offset < 0:
            adj_times = ['' for i in range(-self.timewin.offset)]
            adj_times.extend(self.rawtimes['times'])
            adj_ids = list(self.rawtimes['ids'])
        printed_ids = set([self.junkid]) #keep track of the ones we've already seen
        # We will write the alltimes csv online, while storing up the strings for the div results, so they can be properly headered
        with open(os.sep.join([self.path, self.path+'_'+self.timewin.timestr+'_alltimes.csv']), 'w') as fout:
            # Write out the header
            fout.write(tablehead)
            for (tag, time) in sorted(zip(adj_ids, self.rawtimes['times']), key=lambda entry: entry[1]):
                if tag and time and tag not in printed_ids:
                    printed_ids.add(tag)
                    age = self.timing[tag]['Age']
                    gen = self.timing[tag]['Gender']
                    # Our table entry will be the same for both full results and divisionals, except for the place.
                    tableentry = ','+time+','+self.timing[tag]['First name']+' '+self.timing[tag]['Last name']+','+tag+','+gen+','+age
                    for colname in colnames:
                        tableentry += ','+self.timing[tag][colname]
                    tableentry += '\n'
                    fout.write(str(allplace)+tableentry)
                    allplace += 1
                    # and the appropriate divisional result
                    try:
                        age = int(age)
                    except ValueError:
                        age = ''
                    # Now we go through the divisions
                    for (divindx, div) in enumerate(self.divisions):
                        # First check age.
                        divcheck = True
                        for field in div[1]:
                            if field == 'Age':
                                if not age:
                                    divcheck = False
                                elif age < div[1]['Age'][0] or age > div[1]['Age'][1]:
                                    divcheck = False
                            else:
                                if self.timing[tag][field] != div[1][field]:
                                    divcheck = False
                        # Now add this result to the div results, if it satisfied the requirements
                        if divcheck:
                            divresults[divindx] += str(divplace[divindx])+tableentry
                            divplace[divindx] += 1
        # Now write out the divisional results
        with open(os.sep.join([self.path, self.path+'_'+self.timewin.timestr+'_divtimes.csv']), 'w') as fout:
            for i, divresult in enumerate(divresults):
                if divplace[i] > 1:
                    fout.write(divresult)
        md = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, "Results saved to csv!")
        md.run()
        md.destroy()

    def print_times_html_laps(self):
        '''Prints the current time results to a nice html table for races with laps.
           the entire table is reformed every time,
           so this may get slow for a large number of racers ?'''
        # Figure out what the columns will be, other than id/age/gender
        colnames = [field for div in self.divisions for field in div[1]]
        colnames = set(colnames)
        if 'Age' in colnames:
            colnames.remove('Age')
        if 'Gender' in colnames:
            colnames.remove('Gender')
        # We will only add these columns if they aren't too long (to overflow the page). We allow up to a total of 20 characters.
        if sum([len(colname) for colname in colnames]) > 15:
            colnames = []
        # Now begin to construct strings
        # The first string will be all of the head information for the html page, including the css styles.
        htmlhead = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <style type="text/css">
        #tab
        {
                font-family: Sans-Serif;
                font-size: 14px;
                margin: 20px;
                width: 650px;
                text-align: left;
        }
        #tab th
        {
                font-size: 15px;
                font-weight: bold;
                padding: 10px 8px;
                border-bottom: 2px solid gray;
        }
        #tab td
        {
                border-bottom: 1px solid #ccc;
                padding: 6px 8px;
        }
        #footer{ margin-top: 20px; margin-left: 20px; font: 10px sans-serif;}
        </style>
        </head>
        <body>\n"""
        # the second string will be the beginning of a table.
        tablehead = """<table id="tab">
        <thead>
        <tr>
        <th scope="col">Place</th>
        <th scope="col">Time</th>
        <th scope="col">Lap times</th>
        <th scope="col">Name</th>
        <th scope="col">Bib ID</th>
        <th scope="col">Gender</th>
        <th scope="col">Age</th>"""
        # And now the extra column names
        for colname in colnames:
            tablehead += '<th scope="col">'+colname+'</th>'
        # Now continue on
        tablehead += """</tr></thead><tbody>\n"""
        tablefoot = '</tbody></table>'
        htmlfoot = '<div id="footer">Race timing with fsTimer - free, open source software for race timing. http://fstimer.org</div></body></html>'
        # First we prepare the fullresults string.
        fullresults = htmlhead+tablehead
        # and each of the division results
        divresults = ['<span style="font-size:22px">'+div[0]+'</span>\n'+tablehead for div in self.divisions]
        allplace = 1
        divplace = [1 for div in self.divisions]
        # go through the data from fastest time to slowest
        if self.timewin.offset >= 0:
            adj_ids = ['' for i_unused in range(self.timewin.offset)]
            adj_ids.extend(self.rawtimes['ids'])
            adj_times = list(self.rawtimes['times'])
        elif self.timewin.offset < 0:
            adj_times = ['' for i_unused in range(-self.timewin.offset)]
            adj_times.extend(self.rawtimes['times'])
            adj_ids = list(self.rawtimes['ids'])
        laptimesdic = defaultdict(list)
        # We do a run through all of the times and group lap times
        for (tag, time) in sorted(zip(adj_ids, adj_times), key=lambda entry: entry[1]):
            if tag and time and tag != self.junkid:
                d1 = re.match(r'((?P<days>\d+) days, )?(?P<hours>\d+):'r'(?P<minutes>\d+):(?P<seconds>\d+)', time).groupdict(0) #convert txt time to dict
                laptimesdic[tag].append(datetime.timedelta(**dict(((key, int(value)) for key, value in d1.items())))) #convert dict time to datetime, and store
        # Each value of laptimesdic is a list, sorted in order from fastest time (1st lap) to longest time (last lap).
        # Go through and compute the lap times.
        laptimesdic2 = defaultdict(list)
        for tag, times in laptimesdic.iteritems():
            # First put the total race time
            if len(laptimesdic[tag]) == self.numlaps:
                laptimesdic2[tag] = [str(laptimesdic[tag][-1])]
            else:
                laptimesdic2[tag] = ['<>']
            # And now the first lap
            laptimesdic2[tag].append(str(laptimesdic[tag][0]))
            # And now the subsequent laps
            laptimesdic2[tag].extend([str(laptimesdic[tag][ii+1] - laptimesdic[tag][ii]) for ii in range(len(laptimesdic[tag])-1)])
        # Now run through the data one more time and print the results.
        for (tag, times) in sorted(laptimesdic2.items(), key=lambda entry: entry[1][0]):
            age = self.timing[tag]['Age']
            gen = self.timing[tag]['Gender']
            # Our table entry will be the same for both full results and divisionals, except for the place.
            # First the total time and first lap
            tableentry = '</td><td>' + times[0] + '</td><td>1 - ' + times[1] + \
              '</td><td>' + self.timing[tag]['First name'] + ' ' + \
              self.timing[tag]['Last name'] + '</td><td>' + tag + '</td><td>' + \
              gen + '</td><td>' + age + '</td>'
            # And now add in the extra columns
            for colname in colnames:
                tableentry += '<td>'+self.timing[tag][colname]+'</td>'
            tableentry += '</tr>\n'
            # And now the lap times
            for ii in range(2, len(times)):
                tableentry += '<tr><td></td><td></td><td>'+str(ii)+' - '+times[ii]+'</td><td></td><td></td><td></td><td></td>'
                #And now add in the extra columns
                for colname in colnames:
                    tableentry += '<td>'+self.timing[tag][colname]+'</td>'
                tableentry += '</tr>\n'
            if times[0] != '<>':
                fullresults += '<tr><td>'+str(allplace)+tableentry
            else:
                fullresults += '<tr><td><>'+tableentry
            allplace += 1
            # and the appropriate divisional result
            try:
                age = int(age)
            except ValueError:
                age = ''
            # Now we go through the divisions
            for (divindx, div) in enumerate(self.divisions):
                # First check age.
                divcheck = True
                for field in div[1]:
                    if field == 'Age':
                        if not age:
                            divcheck = False
                        elif age < div[1]['Age'][0] or age > div[1]['Age'][1]:
                            divcheck = False
                    else:
                        if self.timing[tag][field] != div[1][field]:
                            divcheck = False
                # Now add this result to the div results, if it satisfied the requirements
                if divcheck:
                    if times[0] != '<>':
                        divresults[divindx] += '<tr><td>'+str(divplace[divindx])+tableentry
                    else:
                        divresults[divindx] += '<tr><td><>'+tableentry
                    divplace[divindx] += 1
            # And write to file.
            with open(os.sep.join([self.path, self.path+'_'+self.timewin.timestr+'_alltimes.html']), 'w') as fout:
                fout.write(fullresults+tablefoot+htmlfoot)
            with open(os.sep.join([self.path, self.path+'_'+self.timewin.timestr+'_divtimes.html']), 'w') as fout:
                fout.write(htmlhead)
                for (divindx, divstr) in enumerate(divresults):
                    if divplace[divindx] > 1:
                        fout.write(divstr+tablefoot)
                fout.write(htmlfoot)

    def print_times_csv_laps(self):
        '''Prints the current time results to a csv file for races with laps.
           the entire table is reformed every time,
           so this may get slow for a large number of racers ?'''
        # Figure out what the columns will be, other than id/age/gender
        colnames = [field for div in self.divisions for field in div[1]]
        colnames = set(colnames)
        if 'Age' in colnames:
            colnames.remove('Age')
        if 'Gender' in colnames:
            colnames.remove('Gender')
        # Create the header string
        tablehead = 'Place,Time,Lap times,Name,Bib ID,Gender,Age'
        for colname in colnames:
            tablehead += ','+colname
        tablehead += '\n'
        # Keep track of the places
        allplace = 1
        divplace = [1 for div in self.divisions]
        divresults = ['\n'+div[0]+'\n'+tablehead for div in self.divisions]
        # go through the data from fastest time to slowest
        if self.timewin.offset >= 0:
            adj_ids = ['' for i in range(self.timewin.offset)]
            adj_ids.extend(self.rawtimes['ids'])
            adj_times = list(self.rawtimes['times'])
        elif self.timewin.offset < 0:
            adj_times = ['' for i in range(-self.timewin.offset)]
            adj_times.extend(self.rawtimes['times'])
            adj_ids = list(self.rawtimes['ids'])
        laptimesdic = defaultdict(list)
        # We do a run through all of the times and group lap times
        for (tag, time) in sorted(zip(adj_ids, adj_times), key=lambda entry: entry[1]):
            if tag and time and tag != self.junkid:
                d1 = re.match(r'((?P<days>\d+) days, )?(?P<hours>\d+):'r'(?P<minutes>\d+):(?P<seconds>\d+)', time).groupdict(0) #convert txt time to dict
                laptimesdic[tag].append(datetime.timedelta(**dict(((key, int(value)) for key, value in d1.items())))) #convert dict time to datetime, and store
        # Each value of laptimesdic is a list, sorted in order from fastest time (1st lap) to longest time (last lap).
        # Go through and compute the lap times.
        laptimesdic2 = defaultdict(list)
        for tag, times in laptimesdic.iteritems():
            # First put the total race time
            if len(laptimesdic[tag]) == self.numlaps:
                laptimesdic2[tag] = [str(laptimesdic[tag][-1])]
            else:
                laptimesdic2[tag] = ['<>']
            # And now the first lap
            laptimesdic2[tag].append(str(laptimesdic[tag][0]))
            # And now the subsequent laps
            laptimesdic2[tag].extend([str(laptimesdic[tag][ii+1] - laptimesdic[tag][ii]) for ii in range(len(laptimesdic[tag])-1)])
        # Now run through the data one more time and print the results.
        with open(os.sep.join([self.path, self.path+'_'+self.timewin.timestr+'_alltimes.csv']), 'w') as fout:
            fout.write(tablehead)
            for (tag, times) in sorted(laptimesdic2.items(), key=lambda entry: entry[1][0]):
                age = self.timing[tag]['Age']
                gen = self.timing[tag]['Gender']
                # Our table entry will be the same for both full results and divisionals, except for the place.
                # First the total time and first lap
                tableentry = ','+times[0]+',1 - '+times[1]+','+self.timing[tag]['First name']+' '+self.timing[tag]['Last name']+','+tag+','+gen+','+age
                for colname in colnames:
                    tableentry += ','+self.timing[tag][colname]
                tableentry += '\n'
                # And now the lap times
                for ii in range(2, len(times)):
                    tableentry += ',,'+str(ii)+' - '+times[ii]+',,,,'
                    for colname in colnames:
                        tableentry += ','
                    tableentry += '\n'
                if times[0] != '<>':
                    fout.write(str(allplace)+tableentry)
                else:
                    fout.write('<>'+tableentry)
                allplace += 1
                # and the appropriate divisional result
                try:
                    age = int(age)
                except ValueError:
                    age = ''
                # Now we go through the divisions
                for (divindx, div) in enumerate(self.divisions):
                    # First check age.
                    divcheck = True
                    for field in div[1]:
                        if field == 'Age':
                            if not age:
                                divcheck = False
                            elif age < div[1]['Age'][0] or age > div[1]['Age'][1]:
                                divcheck = False
                        else:
                            if self.timing[tag][field] != div[1][field]:
                                divcheck = False
                    #Now add this result to the div results, if it satisfied the requirements
                    if divcheck:
                        if times[0] != '<>':
                            divresults[divindx] += str(divplace[divindx])+tableentry
                        else:
                            divresults[divindx] += '<>'+tableentry
                        divplace[divindx] += 1
        #Now write out the divisional results
        with open(os.sep.join([self.path, self.path+'_'+self.timewin.timestr+'_divtimes.csv']), 'w') as fout:
            for i, divresult in enumerate(divresults):
                if divplace[i] > 1:
                    fout.write(divresult)
