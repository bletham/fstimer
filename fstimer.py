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


import pygtk
pygtk.require('2.0')
import gtk
import os,re,time,json,datetime,sys,csv,string
import fstimer.gui.intro, fstimer.gui.newproject, fstimer.gui.definefields, fstimer.gui.definefamilyreset, fstimer.gui.definedivisions, fstimer.gui.root, fstimer.gui.about, fstimer.gui.importprereg, fstimer.gui.preregister, fstimer.gui.register, fstimer.gui.compile, fstimer.gui.compileerrors, fstimer.gui.pretime
from collections import defaultdict

class PyTimer:
  
  def __init__(self):
    self.bgcolor = fstimer.gui.bgcolor
    self.introwin = fstimer.gui.intro.IntroWin(self.load_project,
                                               self.create_project)
    self.prereg = []
    
  #Here we have selected a project with combobox from intro window. We define path, load the registration settings, and goto rootwin
  def load_project(self,jnk,combobox,projectlist):
    self.path = projectlist[combobox.get_active()]
    with open(os.sep.join([self.path,self.path+'.reg']),'rb') as fin:
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

  def create_project(self, jnk):
    '''creates a new project'''
    self.newprojectwin = fstimer.gui.newproject.NewProjectWin(self.define_fields,
                                                              self.introwin)

  def define_fields(self, jnk_unused):
    '''Handled the definition of fields when creating a new project'''
    #this is really just fsTimer.fieldsdic.keys(), but is important because it defines the order in which fields show up on the registration screen
    self.fields = ['Last name', 'First name', 'ID', 'Age', 'Gender',
                          'Address', 'Email', 'Telephone', 'Contact for future races',
                          'How did you hear about race']
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
  
  def back_to_new_project(self,jnk):
    self.definefieldswin.hide()
    self.newprojectwin.show_all()
    
  def define_family_reset(self,jnk):
    self.definefieldswin.hide()
    self.familyresetwin = fstimer.gui.definefamilyreset.FamilyResetWin \
      (self.fields, self.back_to_define_fields, self.define_divisions, self.introwin)

  def back_to_define_fields(self,jnk):
    self.familyresetwin.hide()
    self.definefieldswin.show_all()
    
  def define_divisions(self,jnk,btnlist):
    self.clear_for_fam = []
    for (field,btn) in zip(self.fields,btnlist):
      if btn.get_active():
        self.clear_for_fam.append(field)
    self.familyresetwin.hide()
    #Here we specify the default divisions.
    self.divisions = []
    self.divisions.append(('Female, ages 10 and under',{'Gender':'female','Age':(0,10)}))
    self.divisions.append(('Male, ages 10 and under',{'Gender':'male','Age':(0,10)}))
    for i in range(13):
      for gender in ['Female','Male']:
        minage = 10+i*5
        maxage = 10+i*5+4
        divname = gender+', ages '+str(minage)+'-'+str(maxage)
        self.divisions.append((divname,{'Gender':gender.lower(),'Age':(minage,maxage)}))
    self.divisions.append(('Female, ages 80 and up',{'Gender':'female','Age':(80,120)}))
    self.divisions.append(('Male, ages 80 and up',{'Gender':'male','Age':(80,120)}))
    self.divisionswin = fstimer.gui.definedivisions.DivisionsWin \
      (self.fields, self.fieldsdic, self.divisions, self.back_to_define_fields2, self.store_new_project, self.introwin)
      
  def back_to_define_fields2(self,jnk):
    self.divisionswin.hide()
    self.definefieldswin.show_all()
    return
    
  def store_new_project(self,jnk):
    os.system('mkdir '+self.path)
    regdata = {}
    regdata['fields'] = self.fields
    regdata['fieldsdic'] = self.fieldsdic
    regdata['clear_for_fam'] = self.clear_for_fam
    regdata['divisions'] = self.divisions
    with open(os.sep.join([self.path, self.path+'.reg']),'wb') as fout:
      json.dump(regdata,fout)
    md = gtk.MessageDialog(self.divisionswin,gtk.DIALOG_MODAL,gtk.MESSAGE_INFO,gtk.BUTTONS_OK,'Project '+self.path+' successfully created!')
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
    self.preregistrationwin = fstimer.gui.preregister.PreRegistrationWin(os.getcwd(), self.path, lambda fn: self.set_registration_file(fn), self.handle_registration)

  def set_registration_file(self, filename):
    '''set a preregistration file'''
    with open(filename,'rb') as fin:
      self.prereg = json.load(fin)

  def handle_registration(self, jnk_unused, regid_btn):
    '''handles registration'''
    self.regid = regid_btn.get_value_as_int()
    self.preregistrationwin.hide()
    self.registrationwin = fstimer.gui.register.RegistrationWin(self.path, self.fields, self.fieldsdic, self.prereg, self.clear_for_fam, self.save_registration)

  def save_registration(self):
    '''saves registration'''
    filename = os.sep.join([self.path,self.path+'_registration_'+str(self.regid)+'.json'])
    with open(filename, 'wb') as fout:
      json.dump(self.prereg,fout)
    return filename

  def compreg_window(self,jnk):
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
      with open(fname,'rb') as fin:
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

  #Here we no longer have any errors (either we had none to begin with, or we have corrected them all)
  #We write the dictionaries to the disk
  #We also write a csv
  def compreg_noerrors(self,errs=False):
    if errs:
      self.compilewin.setLabel(1, '<span color="blue">Checking for errors... errors corrected.</span>')
    else:
      self.compilewin.setLabel(1, '<span color="blue">Checking for errors... no errors found!</span>')
    #Now save things
    with open(os.sep.join([self.path, self.path+'_registration_compiled.json']),'wb') as fout:
      json.dump(self.reg_nodups,fout)
    with open(os.sep.join([self.path, self.path+'_timing_dict.json']),'wb') as fout:
      json.dump(self.timedict,fout)
    self.compilewin.setLabel(2, '<span color="blue">Successfully wrote files:\n'+os.sep.join([self.path, self.path+'_registration_compiled.json'])+'\n'+os.sep.join([self.path, self.path+'_timing_dict.json'])+'</span>')
    #And write the compiled registration to csv
    with open(os.sep.join([self.path, self.path+'_registration.csv']),'wb') as fout:
      dict_writer = csv.DictWriter(fout,self.fields)
      dict_writer.writer.writerow(self.fields)
      dict_writer.writerows(self.reg_nodups)
    return
    
  def gen_pretimewin(self,jnk):
    # Selects a timing dictionary to use
    self.timing = defaultdict(lambda: defaultdict(str))
    self.pretimewin = fstimer.gui.pretime.PreTimeWin(self.path, self.timing, self.gen_timewin)
        
  # Timing window --------------------------------------------------------------------------
  #Now we actually do the timing!
  def gen_timewin(self,jnk,entry1,timebtncombobox,timebtnlist,check_button,check_button2,numlapsbtn):
    self.junkid = entry1.get_text()
    self.timebtn = timebtnlist[timebtncombobox.get_active()]
    if check_button.get_active():
      self.strpzeros = True
    else:
      self.strpzeros = False
    if check_button2.get_active():
      self.numlaps = numlapsbtn.get_value_as_int()
    else:
      self.numlaps = 1
    #we're done with pretiming
    self.pretimewin.hide()
    #Prepare the window
    self.timewin = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.timewin.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
    self.timewin.set_transient_for(self.rootwin)
    self.timewin.set_modal(True)
    self.timewin.set_title('fsTimer - '+self.path)
    self.timewin.set_position(gtk.WIN_POS_CENTER)
    self.timewin.connect('delete_event',lambda b,jnk: self.done_timing(b))
    self.timewin.set_border_width(10)
    self.timewin.set_size_request(450, 450)
    #We will put the timing info in a liststore in a scrolledwindow
    self.timemodel = gtk.ListStore(str,str)
    #We will put the liststore in a treeview
    self.timeview = gtk.TreeView()
    column = gtk.TreeViewColumn('ID',gtk.CellRendererText(),text=0)
    self.timeview.append_column(column)
    column = gtk.TreeViewColumn('Time',gtk.CellRendererText(),text=1)
    self.timeview.append_column(column)
    self.timeview.set_model(self.timemodel)
    self.timeview.connect('size-allocate',self.scroll_times)
    treeselection = self.timeview.get_selection()
    treeselection.set_mode(gtk.SELECTION_MULTIPLE) #make it multiple selecting
    #And put it in a scrolled window, in an alignment
    self.timesw = gtk.ScrolledWindow()
    self.timesw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
    self.timesw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.timesw.add(self.timeview)
    timealgn = gtk.Alignment(0,0,1,1)
    timealgn.add(self.timesw)
    self.entrybox = gtk.Entry(max=40)
    #We will store 'raw' data, lists of times and IDs.
    self.rawtimes = {}
    self.rawtimes['times'] = []
    self.rawtimes['ids'] = []
    self.offset = 0 #this is len(times) - len(ids)
    self.entrybox.connect('activate',self.record_time)
    self.entrybox.connect('changed',self.check_for_newtime)
    #And we will save our file as,
    self.timestr = re.sub(' +','_',time.ctime()).replace(':','')
    #Now lets go on to boxes
    tophbox = gtk.HBox()
    #our default t0, and the stuff on top for setting/edit t0
    self.t0 = 0.
    btn_t0 = gtk.Button('Start!')
    btn_t0.connect('clicked',self.set_t0)
    btn_editt0 = gtk.Button(stock=gtk.STOCK_EDIT)
    btn_editt0.connect('clicked',self.edit_t0)
    tophbox.pack_start(btn_t0,False,False,8)
    tophbox.pack_start(btn_editt0,False,False,8)
    self.t0_label = gtk.Label('t0: '+str(self.t0))
    tophbox.pack_start(self.t0_label,True,True,8)
    timevbox1 = gtk.VBox(False,8)
    timevbox1.pack_start(tophbox,False,False,0)
    timevbox1.pack_start(timealgn,True,True,0)
    timevbox1.pack_start(self.entrybox,False,False,0)
    #we will keep track of how many racers are still out.
    self.racers_reg = self.timing.keys()
    self.racers_total = str(len(self.racers_reg))
    self.racers_in = 0
    self.racerslabel = gtk.Label()
    self.racerslabel.set_markup(str(self.racers_in)+' racers checked in out of '+self.racers_total+' registered.')
    timevbox1.pack_start(self.racerslabel,False,False,0)
    vbox1align = gtk.Alignment(0,0,1,1)
    vbox1align.add(timevbox1)
    #buttons on the right side
    btnDROPID = gtk.Button('Drop ID')
    btnDROPID.connect('clicked',self.timing_rm_ID)
    btnDROPTIME = gtk.Button('Drop time')
    btnDROPTIME.connect('clicked',self.timing_rm_time)
    btnEDIT = gtk.Button(stock=gtk.STOCK_EDIT)
    btnEDIT.connect('clicked',self.edit_time)
    btnPRINT = gtk.Button(stock=gtk.STOCK_PRINT)
    btnPRINT.connect('clicked',self.print_times)
    btnSAVE = gtk.Button(stock=gtk.STOCK_SAVE)
    btnSAVE.connect('clicked',self.save_times)
    btnCSV = gtk.Button('Save CSV')
    btnCSV.connect('clicked',self.print_times_csv)
    btnRESUME = gtk.Button('Resume')
    btnRESUME.connect('clicked',self.resume_times)
    btnOK = gtk.Button('Done')
    btnOK.connect('clicked', self.done_timing)
    vsubbox = gtk.VBox(False,8)
    vsubbox.pack_start(btnDROPID,False,False,0)
    vsubbox.pack_start(btnDROPTIME,False,False,0)
    vsubbox.pack_start(btnEDIT,False,False,40)
    vsubbox.pack_start(btnPRINT,False,False,0)
    vsubbox.pack_start(btnSAVE,False,False,0)
    vsubbox.pack_start(btnCSV,False,False,0)
    vsubbox.pack_start(btnRESUME,False,False,0)
    vsubbox.pack_start(btnOK,False,False,0)
    vspacer = gtk.Alignment(1, 1, 0, 0)
    vspacer.add(vsubbox)
    timehbox = gtk.HBox(False,8)
    timehbox.pack_start(vbox1align,True,True,0)
    timehbox.pack_start(vspacer,False,False,0)
    self.timewin.add(timehbox)
    self.timewin.show_all()
    return
    
  def check_for_newtime(self,jnk):
    if self.entrybox.get_text() == self.timebtn:
      self.new_blank_time()
    return
    
  def scroll_times(self,jnk1,jnk2):
    adj = self.timesw.get_vadjustment()
    adj.set_value(0)
    return
  
  #Here we have pressed start. We set t0 to the current time.
  def set_t0(self,jnk):
    self.t0 = time.time()
    self.t0_label.set_markup('t0: '+str(self.t0))
    return
  
  #Here we have chosen to edit t0. Load up a window and query the new t0.
  def edit_t0(self,jnk):
    self.t0win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.t0win.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
    self.t0win.set_title('fsTimer - '+self.path)
    self.t0win.set_position(gtk.WIN_POS_CENTER)
    self.t0win.set_transient_for(self.timewin)
    self.t0win.set_modal(True)
    self.t0win.connect('delete_event',lambda b,jnk: self.t0win.hide())
    self.t0box = gtk.Entry()
    self.t0box.set_text(str(self.t0))
    hbox = gtk.HBox(False,8)
    btnOK = gtk.Button(stock=gtk.STOCK_OK)
    btnOK.connect('clicked',self.ok_editt0)
    btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
    btnCANCEL.connect('clicked', lambda jnk: self.t0win.hide())
    hbox.pack_start(btnOK,False,False,8)
    hbox.pack_start(btnCANCEL,False,False,8)
    vbox = gtk.VBox(False,8)
    vbox.pack_start(self.t0box,False,False,8)
    vbox.pack_start(hbox,False,False,8)
    self.t0win.add(vbox)
    self.t0win.show_all()
    return
    
  #Here we have edited t0 and pressed OK. Set the new t0.
  def ok_editt0(self,jnk):
    self.t0 = float(self.t0box.get_text())
    self.t0_label.set_markup('t0: '+str(self.t0))
    self.t0win.hide()
    return
  
  #This chooses which edit time window to open, depending on how many items are selected
  def edit_time(self,jnk):
    treeselection = self.timeview.get_selection()
    model, pathlist = treeselection.get_selected_rows()
    if len(pathlist) == 0:
      pass #we don't load any windows or do anything
    elif len(pathlist) == 1:
      #load the edit_single window
      self.edit_single_time(self.timemodel.get_iter(pathlist[0]))
    else:
      #We are block-editing; load the block-editing window.
      self.edit_block_times(pathlist)
    return
  
  #This loads the edit single time window
  def edit_single_time(self,treeiter1):
    old_id,old_time = self.timemodel.get(treeiter1,0,1)
    self.winedittime = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.winedittime.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
    self.winedittime.set_transient_for(self.timewin)
    self.winedittime.set_modal(True)
    self.winedittime.set_title('fsTimer - Edit time')
    self.winedittime.set_position(gtk.WIN_POS_CENTER)
    self.winedittime.set_border_width(20)
    self.winedittime.connect('delete_event',lambda b,jnk: self.winedittime.hide())
    label0 = gtk.Label('')
    label0.set_markup('<span color="red">WARNING: Changes to these values cannot be automatically undone</span>\nIf you change the time and forget the old one, it will be gone forever.')
    label1 = gtk.Label('ID:')
    entryid = gtk.Entry(max=6)
    entryid.set_text(old_id)
    hbox1 = gtk.HBox(False,10)
    hbox1.pack_start(label1,False,False,0)
    hbox1.pack_start(entryid,False,False,0)
    label2 = gtk.Label('Time:')
    entrytime = gtk.Entry(max=25)
    entrytime.set_text(old_time)
    hbox2 = gtk.HBox(False,10)
    hbox2.pack_start(label2,False,False,0)
    hbox2.pack_start(entrytime,False,False,0)
    btnOK = gtk.Button(stock=gtk.STOCK_OK)
    btnOK.connect('clicked',self.winedittimeOK,treeiter1,entryid,entrytime,old_id,old_time)
    btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
    btnCANCEL.connect('clicked',lambda b: self.winedittime.hide())
    cancel_algn = gtk.Alignment(0,0,0,0)
    cancel_algn.add(btnCANCEL)
    hbox3 = gtk.HBox(False,10)
    hbox3.pack_start(cancel_algn,True,True,0)
    hbox3.pack_start(btnOK,False,False,0)
    vbox = gtk.VBox(False,10)
    vbox.pack_start(label0,False,False,10)
    vbox.pack_start(hbox1,False,False,0)
    vbox.pack_start(hbox2,False,False,0)
    vbox.pack_start(hbox3,False,False,0)
    self.winedittime.add(vbox)
    self.winedittime.show_all()
    return
  
  #This stores times that have been modified using the "Edit" button and the single edit window
  def winedittimeOK(self,jnk,treeiter,entryid,entrytime,old_id,old_time):
    new_id = entryid.get_text()
    new_time = entrytime.get_text()
    row = self.timemodel.get_path(treeiter)
    row = row[0]
    if row < self.offset:
      if new_id:
        #we are putting an ID in a slot that we hadn't reached yet. Fill in any other missing ones up to this point with ''.
        ids = [str(new_id)]
        ids.extend(['' for i in range(self.offset-row-1)])
        ids.extend(self.rawtimes['ids'])
        self.rawtimes['ids'] = list(ids)
        self.offset = row #the new offset
        self.rawtimes['times'][row] = str(new_time) #the new time
        self.timemodel.set_value(treeiter,0,str(new_id))
        self.timemodel.set_value(treeiter,1,str(new_time))
      elif new_time:
        #we are adjusting the time only.
        self.rawtimes['times'][row] = str(new_time) #the new time
        self.timemodel.set_value(treeiter,1,str(new_time))
      else:
        #we are clearing this entry. pop it from time and adjust offset.
        self.rawtimes['times'].pop(row)
        self.offset-=1
        self.timemodel.remove(treeiter)
    elif row == self.offset and new_time and not new_id:
      #then we are clearing the most recent ID. We pop it and adjust self.offset and adjust the time.
      self.rawtimes['ids'].pop(0)
      self.rawtimes['times'][row] = str(new_time)
      self.offset+=1
      self.timemodel.set_value(treeiter,0,str(new_id))
      self.timemodel.set_value(treeiter,1,str(new_time))
    elif row < -self.offset:
      #Here we are making edits to a slot where there is an ID, but no time.
      if new_time:
        #we are putting a time in a slot that we hadn't reached yet. Fill in any other missing ones up to this point with blanks.
        times = [str(new_time)]
        times.extend(['' for i in range(-self.offset-row-1)])
        times.extend(self.rawtimes['times'])
        self.rawtimes['times'] = list(times)
        self.offset = -row #the new offset
        self.rawtimes['ids'][row] = str(new_id) #the new time
        self.timemodel.set_value(treeiter,0,str(new_id))
        self.timemodel.set_value(treeiter,1,str(new_time))
      elif new_id:
        #we are adjusting the id only.
        self.rawtimes['ids'][row] = str(new_id) #the new time
        self.timemodel.set_value(treeiter,0,str(new_id))
      else:
        #we are clearing this entry. pop it from id and adjust offset.
        self.rawtimes['ids'].pop(row)
        self.offset+=1
        self.timemodel.remove(treeiter)
    else:
      if not new_time and not new_id:
        #we are clearing the entry
        if self.offset > 0:
          self.rawtimes['ids'].pop(row-self.offset)
          self.rawtimes['times'].pop(row)
        elif self.offset <= 0:
          self.rawtimes['ids'].pop(row)
          self.rawtimes['times'].pop(row+self.offset)
        self.timemodel.remove(treeiter)
      else:
        #adjust the entry
        if self.offset>0:
          self.rawtimes['ids'][row-self.offset] = str(new_id)
          self.rawtimes['times'][row] = str(new_time)
        elif self.offset <= 0:
          self.rawtimes['ids'][row] = str(new_id)
          self.rawtimes['times'][row+self.offset] = str(new_time)
        self.timemodel.set_value(treeiter,0,str(new_id))
        self.timemodel.set_value(treeiter,1,str(new_time))
    self.winedittime.hide()
    return
    
   #This loads the edit block times window
  def edit_block_times(self,pathlist):
    self.wineditblocktime = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.wineditblocktime.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
    self.wineditblocktime.set_transient_for(self.timewin)
    self.wineditblocktime.set_modal(True)
    self.wineditblocktime.set_title('fsTimer - Edit times')
    self.wineditblocktime.set_position(gtk.WIN_POS_CENTER)
    self.wineditblocktime.set_border_width(20)
    self.wineditblocktime.connect('delete_event',lambda b,jnk: self.wineditblocktime.hide())
    label0 = gtk.Label('')
    label0.set_markup('<span color="red">WARNING: Changes to times cannot be automatically undone</span>\nIf you change the times and forget the old values, they will be gone forever.')
    label1 = gtk.Label('Time (h:mm:ss) to be added or subtracted from all selected times:')
    radiobutton = gtk.RadioButton(None, "ADD")
    radiobutton.set_active(True)
    radiobutton2 = gtk.RadioButton(radiobutton, "SUBTRACT")
    entrytime = gtk.Entry(max=7)
    entrytime.set_text('0:00:00')
    hbox1 = gtk.HBox(False,10)
    hbox1.pack_start(radiobutton,False,False,0)
    hbox1.pack_start(radiobutton2,False,False,0)
    hbox1.pack_start(entrytime,False,False,0)
    btnOK = gtk.Button(stock=gtk.STOCK_OK)
    btnOK.connect('clicked',self.wineditblocktimesOK,pathlist,radiobutton,entrytime)
    btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
    btnCANCEL.connect('clicked',lambda b: self.wineditblocktime.hide())
    cancel_algn = gtk.Alignment(0,0,0,0)
    cancel_algn.add(btnCANCEL)
    hbox2 = gtk.HBox(False,10)
    hbox2.pack_start(cancel_algn,True,True,0)
    hbox2.pack_start(btnOK,False,False,0)
    vbox = gtk.VBox(False,10)
    vbox.pack_start(label0,False,False,10)
    vbox.pack_start(label1,False,False,10)
    vbox.pack_start(hbox1,False,False,0)
    vbox.pack_start(hbox2,False,False,0)
    self.wineditblocktime.add(vbox)
    self.wineditblocktime.show_all()
    return
  
  #This stores times that have been modified using the "Edit" button and the single edit window
  def wineditblocktimesOK(self,jnk,pathlist,radiobutton,entrytime):
    #Grab which radiobutton was selected ("ADD" or "SUBTRACT")
    radioselection = [r.get_label() for r in radiobutton.get_group() if r.get_active()][0]
    #Now we go through every time in pathlist and do the requested operation
    for path in pathlist:
      #Figure out which row this is, and which treeiter
      treeiter = self.timemodel.get_iter(path)
      row = path[0]
      #Now figure out the new time. First get the old time.
      old_time_str = self.timemodel.get_value(treeiter,1) #the old time, as a string
      #Now we convert it to timedelta
      try:
        d = re.match(r'((?P<days>\d+) days, )?(?P<hours>\d+):'r'(?P<minutes>\d+):(?P<seconds>\d+)',str(old_time_str)).groupdict(0)
        old_time = datetime.timedelta(**dict(( (key, int(value)) for key, value in d.items() )))
        #Now the time adjustment
        adj_time_str = entrytime.get_text() #the input string
        dadj = re.match(r'((?P<days>\d+) days, )?(?P<hours>\d+):'r'(?P<minutes>\d+):(?P<seconds>\d+)',str(adj_time_str)).groupdict(0)
        adj_time = datetime.timedelta(**dict(( (key, int(value)) for key, value in dadj.items() )))
        #Combine the timedeltas to get the new time
        if radioselection == 'ADD':
          new_time = str(old_time + adj_time)
        elif radioselection == 'SUBTRACT':
          if old_time > adj_time:
            new_time = str(old_time - adj_time)
          else:
            new_time = '0:00:00' #We don't allow negative times.
        #And save them, and write out to the timemodel
        self.rawtimes['times'][row] = str(new_time) #the new time
        self.timemodel.set_value(treeiter,1,str(new_time))
        #Continue on to the next path
      except AttributeError:
        #This will happen for instance if the path has a blank time
        pass
    self.wineditblocktime.hide()
    return
  
  #Here we have chosen to remove an ID from the timing window.
  #Throw up an 'are you sure' dialog box, and drop if yes.
  def timing_rm_ID(self,jnk):
    treeselection = self.timeview.get_selection()
    model, pathlist = treeselection.get_selected_rows()
    if len(pathlist) == 0:
      pass #we don't load any windows or do anything
    elif len(pathlist) > 1:
      pass #this is a one-at-a-time operation
    elif len(pathlist) == 1:
      #Figure out what row this is in the timeview
      row = pathlist[0][0]
      #Now figure out what index in self.rawtimes['ids'] it is.
      ididx = row-max(0,self.offset)
      if ididx >= 0:
        #Otherwise, there is no ID here so there is nothing to do.
        #Ask if we are sure.
        rmID_dialog = gtk.MessageDialog(self.timewin,gtk.DIALOG_MODAL,gtk.MESSAGE_QUESTION,gtk.BUTTONS_YES_NO,'Are you sure you want to drop this ID and shift all later IDs down earlier in the list?\nThis cannot be undone.')
        rmID_dialog.set_title('Woah!')
        rmID_dialog.set_default_response(gtk.RESPONSE_NO)
        response = rmID_dialog.run()
        rmID_dialog.destroy()
        if response == gtk.RESPONSE_YES:
          #Make the shift in self.rawtimes and self.offset
          self.rawtimes['ids'].pop(ididx)
          self.offset += 1
          #And now shift everything on the display.
          rowcounter = int(row)
          for i in range(ididx-1,-1,-1):
            #Write rawtimes[i] into row rowcounter
            treeiter = self.timemodel.get_iter((rowcounter,))
            self.timemodel.set_value(treeiter,0,str(self.rawtimes['ids'][i]))
            rowcounter -= 1
          #Now we tackle the last value - there are two possibilities.
          if self.offset > 0:
            #There is a buffer of times, and this one should be cleared.
            treeiter = self.timemodel.get_iter((rowcounter,))
            self.timemodel.set_value(treeiter,0,'')
          else:
            #there is a blank row at the top which should be removed.
            treeiter = self.timemodel.get_iter((rowcounter,))
            self.timemodel.remove(treeiter)
    #All done!
    return
  
  #Here we have chosen to remove a time from the timing window.
  #Throw up an 'are you sure' dialog box, and drop if yes.
  def timing_rm_time(self,jnk):
    treeselection = self.timeview.get_selection()
    model, pathlist = treeselection.get_selected_rows()
    if len(pathlist) == 0:
      pass #we don't load any windows or do anything
    elif len(pathlist) > 1:
      pass #this is a one-at-a-time operation
    elif len(pathlist) == 1:
       #Figure out what row this is in the timeview
      row = pathlist[0][0]
      #Now figure out what index in self.rawtimes['times'] it is.
      timeidx = row-max(0,-self.offset)
      if timeidx >= 0:
        #Otherwise, there is no time here so there is nothing to do.
        #Ask if we are sure.
        rmtime_dialog = gtk.MessageDialog(self.timewin,gtk.DIALOG_MODAL,gtk.MESSAGE_QUESTION,gtk.BUTTONS_YES_NO,'Are you sure you want to drop this time and shift all later times down earlier in the list?\nThis cannot be undone.')
        rmtime_dialog.set_title('Woah!')
        rmtime_dialog.set_default_response(gtk.RESPONSE_NO)
        response = rmtime_dialog.run()
        rmtime_dialog.destroy()
        if response == gtk.RESPONSE_YES:
          #Make the shift in self.rawtimes and self.offset
          self.rawtimes['times'].pop(timeidx)
          self.offset -= 1
          #And now shift everything on the display.
          rowcounter = int(row)
          for i in range(timeidx-1,-1,-1):
            #Write rawtimes[i] into row rowcounter
            treeiter = self.timemodel.get_iter((rowcounter,))
            self.timemodel.set_value(treeiter,1,str(self.rawtimes['times'][i]))
            rowcounter -= 1
          #Now we tackle the last value - there are two possibilities.
          if self.offset < 0:
            #There is a buffer of IDs, and this one should be cleared.
            treeiter = self.timemodel.get_iter((rowcounter,))
            self.timemodel.set_value(treeiter,1,'')
          else:
            #there is a blank row at the top which should be removed.
            treeiter = self.timemodel.get_iter((rowcounter,))
            self.timemodel.remove(treeiter)
    #All done!
    return
  
  #Here we have chosen to resume a timing session
  def resume_times(self,jnk):
    chooser = gtk.FileChooserDialog(title='Choose timing results to resume',action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))
    self.pwd = os.getcwd()
    chooser.set_current_folder(os.sep.join([self.pwd, self.path]))
    ffilter = gtk.FileFilter()
    ffilter.set_name('Timing results')
    ffilter.add_pattern('*_times.json')
    chooser.add_filter(ffilter)
    response = chooser.run()
    if response == gtk.RESPONSE_OK:
      filename = chooser.get_filename()
      try:
        with open(filename,'rb') as fin:
          saveresults = json.load(fin)
        self.rawtimes = saveresults['rawtimes']
        self.timestr = saveresults['timestr']
        self.t0 = saveresults['t0']
        self.t0_label.set_markup('t0: '+str(self.t0))
        self.offset = len(self.rawtimes['times']) - len(self.rawtimes['ids'])
        #Compute how many racers have checked in
        for ID in self.rawtimes['ids']:
          try:
            self.racers_reg.remove(ID)
            self.racers_in += 1
          except ValueError:
            pass
        #And add them to the display.
        self.racerslabel.set_markup(str(self.racers_in)+' racers checked in out of '+self.racers_total+' registered.')
        self.timemodel.clear()
        if self.offset >= 0:
          adj_ids = ['' for i in range(self.offset)]
          adj_ids.extend(self.rawtimes['ids'])
          adj_times = list(self.rawtimes['times'])
        elif self.offset < 0:
          adj_times = ['' for i in range(-self.offset)]
          adj_times.extend(self.rawtimes['times'])
          adj_ids = list(self.rawtimes['ids'])
        for (tag,time) in zip(adj_ids,adj_times):
          self.timemodel.append([tag,time])
        chooser.destroy()
      except (IOError, ValueError, TypeError):
        chooser.destroy()
        error_dialog = gtk.MessageDialog(self.timewin,gtk.DIALOG_MODAL,gtk.MESSAGE_ERROR,gtk.BUTTONS_OK,'ERROR: Failed to resume.')
        error_dialog.set_title('Oops...')
        response = error_dialog.run()
        error_dialog.destroy()
    return
    
  #Here we have chosen to save the times. json dump to the already specified filename.
  def save_times(self,jnk):
    saveresults = {}
    saveresults['rawtimes'] = self.rawtimes
    saveresults['timestr'] = self.timestr
    saveresults['t0'] = self.t0
    with open(os.sep.join([self.path, self.path+'_'+self.timestr+'_times.json']),'wb') as fout:
      json.dump(saveresults,fout)
    md = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, "Times saved!")
    md.run()
    md.destroy()
    return
  
  #Here we have chosen 'OK' on the timing window. Give two dialogs before closing.
  def done_timing(self,jnk):
    if str(type(jnk)) == "<type 'gtk.Button'>":
      oktime_dialog1 = gtk.MessageDialog(None,gtk.DIALOG_MODAL,gtk.MESSAGE_QUESTION,gtk.BUTTONS_YES_NO,'Are you sure you want to leave?')
      oktime_dialog1.set_title('Really done?')
      response1 = oktime_dialog1.run()
      oktime_dialog1.destroy()
    elif str(type(jnk)) == "<type 'gtk.Window'>":
      response1 = gtk.RESPONSE_YES #NOTE this is a cheap hack b/c when called from delete_event the window closes regardless.
    if response1 == gtk.RESPONSE_YES:
      oktime_dialog2 = gtk.MessageDialog(self.timewin,gtk.DIALOG_MODAL,gtk.MESSAGE_QUESTION,gtk.BUTTONS_YES_NO,'Do you want to save before finishing?\nUnsaved data will be lost.')
      oktime_dialog2.set_title('Save?')
      response2 = oktime_dialog2.run()
      oktime_dialog2.destroy()
      if response2 == gtk.RESPONSE_YES:
        self.save_times(None) #this will save.
      self.timewin.hide()
    return
    
  #Here we record times. 
  def new_blank_time(self):
    #Add the current time to the data.
    t = str(datetime.timedelta(seconds=int(time.time()-self.t0)))
    self.rawtimes['times'].insert(0,t) #we prepend to rawtimes, just as we prepend to timemodel
    if self.offset >=0:
      #No IDs in the buffer, so just prepend it to the liststore.
      self.timemodel.prepend(['',t])
    elif self.offset < 0:
      #IDs in the buffer, so add the time to the oldest ID
      self.timemodel.set_value(self.timemodel.get_iter(-self.offset-1),1,t) #put it in the last available ID slot
    self.offset +=1
    self.entrybox.set_text('')
    return
  
  #We have hit enter on the entry box.
  #An ID with times in the buffer gives the oldest (that is, fastest) time in the buffer to the ID
  #An ID with no times in the buffer is added to a buffer of IDs
  #An ID with the marktime symbol in it will first apply the ID and then mark the time.
  def record_time(self,jnk):
    txt = self.entrybox.get_text()
    timemarks = string.count(txt,self.timebtn)
    txt = txt.replace(self.timebtn,'')
    if self.strpzeros:
      txt = txt.lstrip('0')
    #it is actually a result. (or a pass, which we treat as a result)
    #prepend to raw
    self.rawtimes['ids'].insert(0,txt)  
    #and add to the appropriate spot on timemodel.
    if self.offset > 0:
      #we have a time in the store to assign it to
      self.timemodel.set_value(self.timemodel.get_iter(self.offset-1),0,txt) #put it in the last available time slot
    else:
      #It will just be added to the buffer of IDs by prepending to timemodel
      self.timemodel.prepend([txt,''])
    self.offset -=1
    for jnk in range(timemarks):
      self.new_blank_time()
    #And update the racer count.
    try:
      self.racers_reg.remove(txt)
      self.racers_in += 1
      self.racerslabel.set_markup(str(self.racers_in)+' racers checked in out of '+self.racers_total+' registered.')
    except ValueError:
      pass
    self.entrybox.set_text('')
    return
  
  #Here we print the current time results to a nice html table.
  #we reform the entire table every time, so this may get slow for a large number of racers?..
  def print_times(self,jnk):
    if self.numlaps > 1:
      self.print_times_laps()
    else:
      #Figure out what the columns will be, other than id/age/gender
      colnames = [field for div in self.divisions for field in div[1]]
      colnames = set(colnames)
      if 'Age' in colnames:
        colnames.remove('Age')
      if 'Gender' in colnames:
        colnames.remove('Gender')
      #We will only add these columns if they aren't too long (to overflow the page). We allow up to a total of 20 characters.
      if sum([len(colname) for colname in colnames]) > 20:
        colnames = []
      #Now begin to construct strings
      #The first string will be all of the head information for the html page, including the css styles.
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
      #the second string will be the beginning of a table.
      tablehead = """<table id="tab">
      <thead>
      <tr>
      <th scope="col">Place</th>
      <th scope="col">Time</th>
      <th scope="col">Name</th>
      <th scope="col">Bib ID</th>
      <th scope="col">Gender</th>
      <th scope="col">Age</th>"""
      #And now the extra column names
      for colname in colnames:
        tablehead += '<th scope="col">'+colname+'</th>'
      #Now continue on
      tablehead += """</tr></thead><tbody>\n"""
      tablefoot = '</tbody></table>'
      htmlfoot = '<div id="footer">Race timing with fsTimer - free, open source software for race timing. http://fstimer.org</div></body></html>'
      #First we prepare the fullresults string.
      fullresults = htmlhead+tablehead
      #and each of the division results
      divresults = ['<span style="font-size:22px">'+str(div[0])+'</span>\n'+tablehead for div in self.divisions]
      allplace = 1
      divplace = [1 for div in self.divisions]
      #go through the data from fastest time to slowest
      if self.offset >= 0:
        adj_ids = ['' for i in range(self.offset)]
        adj_ids.extend(self.rawtimes['ids'])
        adj_times = list(self.rawtimes['times'])
      elif self.offset < 0:
        adj_times = ['' for i in range(-self.offset)]
        adj_times.extend(self.rawtimes['times'])
        adj_ids = list(self.rawtimes['ids'])
      printed_ids = set([self.junkid]) #keep track of the ones we've already seen
      for (tag,time) in sorted(zip(adj_ids,adj_times), key=lambda entry: entry[1]):
        if tag and time and tag not in printed_ids:
          printed_ids.add(tag)
          age = self.timing[tag]['Age']
          gen = self.timing[tag]['Gender']
          #Our table entry will be the same for both full results and divisionals, except for the place.
          tableentry = '</td><td>'+time+'</td><td>'+self.timing[tag]['First name']+' '+self.timing[tag]['Last name']+'</td><td>'+tag+'</td><td>'+gen+'</td><td>'+age+'</td>'
          #And now add in the extra columns
          for colname in colnames:
            tableentry += '<td>'+self.timing[tag][colname]+'</td>'
          tableentry += '</tr>\n'
          #And add to full results
          fullresults+='<tr><td>'+str(allplace)+tableentry
          allplace +=1
          #and the appropriate divisional result
          try:
            age = int(age)
          except ValueError:
            age = ''
          #Now we go through the divisions
          for (divindx,div) in enumerate(self.divisions):
            #First check age.
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
              divplace[divindx]+=1
        #And write to file.
        with open(os.sep.join([self.path, self.path+'_'+self.timestr+'_alltimes.html']),'w') as fout:
          fout.write(fullresults+tablefoot+htmlfoot)
        with open(os.sep.join([self.path, self.path+'_'+self.timestr+'_divtimes.html']),'w') as fout:
          fout.write(htmlhead)
          for (divindx,divstr) in enumerate(divresults):
            if divplace[divindx] >1:
              fout.write(divstr+tablefoot)
          fout.write(htmlfoot)
    md = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, "Results saved to html!")
    md.run()
    md.destroy()
    return
  
  #Here we print the current time results to a csv file.
  #we reform the entire table every time, so this may get slow for a large number of racers?..
  def print_times_csv(self,jnk):
    if self.numlaps > 1:
      self.print_times_csv_laps()
    else:
      #Figure out what the columns will be, other than id/age/gender
      colnames = [field for div in self.divisions for field in div[1]]
      colnames = set(colnames)
      if 'Age' in colnames:
        colnames.remove('Age')
      if 'Gender' in colnames:
        colnames.remove('Gender')
      #Create the header string
      tablehead = 'Place,Time,Name,Bib ID,Gender,Age'
      for colname in colnames:
        tablehead += ','+colname
      tablehead += '\n'
      #Keep track of the places
      allplace = 1
      divplace = [1 for div in self.divisions]
      divresults = ['\n'+div[0]+'\n'+tablehead for div in self.divisions]
      #go through the data from fastest time to slowest
      if self.offset >= 0:
        adj_ids = ['' for i in range(self.offset)]
        adj_ids.extend(self.rawtimes['ids'])
        adj_times = list(self.rawtimes['times'])
      elif self.offset < 0:
        adj_times = ['' for i in range(-self.offset)]
        adj_times.extend(self.rawtimes['times'])
        adj_ids = list(self.rawtimes['ids'])
      printed_ids = set([self.junkid]) #keep track of the ones we've already seen
      #We will write the alltimes csv online, while storing up the strings for the div results, so they can be properly headered
      with open(os.sep.join([self.path, self.path+'_'+self.timestr+'_alltimes.csv']),'w') as fout:
        #Write out the header
        fout.write(tablehead)
        for (tag,time) in sorted(zip(adj_ids,self.rawtimes['times']), key=lambda entry: entry[1]):
          if tag and time and tag not in printed_ids:
            printed_ids.add(tag)
            age = self.timing[tag]['Age']
            gen = self.timing[tag]['Gender']
            #Our table entry will be the same for both full results and divisionals, except for the place.
            tableentry = ','+time+','+self.timing[tag]['First name']+' '+self.timing[tag]['Last name']+','+tag+','+gen+','+age
            for colname in colnames:
              tableentry += ','+self.timing[tag][colname]
            tableentry+='\n'
            fout.write(str(allplace)+tableentry)
            allplace +=1
            #and the appropriate divisional result
            try:
              age = int(age)
            except ValueError:
              age = ''
            #Now we go through the divisions
            for (divindx,div) in enumerate(self.divisions):
              #First check age.
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
                divresults[divindx] += str(divplace[divindx])+tableentry
                divplace[divindx]+=1
      #Now write out the divisional results
      with open(os.sep.join([self.path, self.path+'_'+self.timestr+'_divtimes.csv']),'w') as fout:
        for i,divresult in enumerate(divresults):
          if divplace[i] > 1:
            fout.write(divresult)
    md = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, "Results saved to csv!")
    md.run()
    md.destroy()
    return
  
  #Here we print the current time results to a nice html table, for races with laps.
  def print_times_laps(self):
    #Figure out what the columns will be, other than id/age/gender
    colnames = [field for div in self.divisions for field in div[1]]
    colnames = set(colnames)
    if 'Age' in colnames:
      colnames.remove('Age')
    if 'Gender' in colnames:
      colnames.remove('Gender')
    #We will only add these columns if they aren't too long (to overflow the page). We allow up to a total of 20 characters.
    if sum([len(colname) for colname in colnames]) > 15:
      colnames = []
    #Now begin to construct strings
    #The first string will be all of the head information for the html page, including the css styles.
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
    #the second string will be the beginning of a table.
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
    #And now the extra column names
    for colname in colnames:
      tablehead += '<th scope="col">'+colname+'</th>'
    #Now continue on
    tablehead += """</tr></thead><tbody>\n"""
    tablefoot = '</tbody></table>'
    htmlfoot = '<div id="footer">Race timing with fsTimer - free, open source software for race timing. http://fstimer.org</div></body></html>'
    #First we prepare the fullresults string.
    fullresults = htmlhead+tablehead
    #and each of the division results
    divresults = ['<span style="font-size:22px">'+div[0]+'</span>\n'+tablehead for div in self.divisions]
    allplace = 1
    divplace = [1 for div in self.divisions]
    #go through the data from fastest time to slowest
    if self.offset >= 0:
      adj_ids = ['' for i in range(self.offset)]
      adj_ids.extend(self.rawtimes['ids'])
      adj_times = list(self.rawtimes['times'])
    elif self.offset < 0:
      adj_times = ['' for i in range(-self.offset)]
      adj_times.extend(self.rawtimes['times'])
      adj_ids = list(self.rawtimes['ids'])
    laptimesdic = defaultdict(list)
    #We do a run through all of the times and group lap times
    for (tag,time) in sorted(zip(adj_ids,adj_times), key=lambda entry: entry[1]):
      if tag and time and tag != self.junkid:
        d1 = re.match(r'((?P<days>\d+) days, )?(?P<hours>\d+):'r'(?P<minutes>\d+):(?P<seconds>\d+)',time).groupdict(0) #convert txt time to dict
        laptimesdic[tag].append(datetime.timedelta(**dict(( (key, int(value)) for key, value in d1.items() )))) #convert dict time to datetime, and store
    #Each value of laptimesdic is a list, sorted in order from fastest time (1st lap) to longest time (last lap).
    #Go through and compute the lap times.
    laptimesdic2 = defaultdict(list)
    for tag,times in laptimesdic.iteritems():
      #First put the total race time
      if len(laptimesdic[tag]) == self.numlaps:
        laptimesdic2[tag] = [str(laptimesdic[tag][-1])]
      else:
        laptimesdic2[tag] = ['<>']
      #And now the first lap
      laptimesdic2[tag].append(str(laptimesdic[tag][0]))
      #And now the subsequent laps
      laptimesdic2[tag].extend([str(laptimesdic[tag][ii+1] - laptimesdic[tag][ii]) for ii in range(len(laptimesdic[tag])-1)])
    #Now run through the data one more time and print the results.
    for (tag,times) in sorted(laptimesdic2.items(), key=lambda entry: entry[1][0]):
      age = self.timing[tag]['Age']
      gen = self.timing[tag]['Gender']
      #Our table entry will be the same for both full results and divisionals, except for the place.
      #First the total time and first lap
      tableentry = '</td><td>'+times[0]+'</td><td>1 - '+times[1]+'</td><td>'+self.timing[tag]['First name']+' '+self.timing[tag]['Last name']+'</td><td>'+tag+'</td><td>'+gen+'</td><td>'+age+'</td>'
      #And now add in the extra columns
      for colname in colnames:
        tableentry += '<td>'+self.timing[tag][colname]+'</td>'
      tableentry+= '</tr>\n'
      #And now the lap times
      for ii in range(2,len(times)):
        tableentry += '<tr><td></td><td></td><td>'+str(ii)+' - '+times[ii]+'</td><td></td><td></td><td></td><td></td>'
        #And now add in the extra columns
        for colname in colnames:
          tableentry += '<td>'+self.timing[tag][colname]+'</td>'
        tableentry+= '</tr>\n'
      if times[0] != '<>':
        fullresults+='<tr><td>'+str(allplace)+tableentry
      else:
        fullresults+='<tr><td><>'+tableentry
      allplace +=1
      #and the appropriate divisional result
      try:
        age = int(age)
      except ValueError:
        age = ''
      #Now we go through the divisions
      for (divindx,div) in enumerate(self.divisions):
        #First check age.
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
            divresults[divindx] += '<tr><td>'+str(divplace[divindx])+tableentry
          else:
            divresults[divindx] += '<tr><td><>'+tableentry
          divplace[divindx]+=1
      #And write to file.
      with open(os.sep.join([self.path, self.path+'_'+self.timestr+'_alltimes.html']),'w') as fout:
        fout.write(fullresults+tablefoot+htmlfoot)
      with open(os.sep.join([self.path, self.path+'_'+self.timestr+'_divtimes.html']),'w') as fout:
        fout.write(htmlhead)
        for (divindx,divstr) in enumerate(divresults):
          if divplace[divindx] >1:
            fout.write(divstr+tablefoot)
        fout.write(htmlfoot)
    return
  
  #Here we print the current time results to a csv file, for races with laps.
  def print_times_csv_laps(self):
    #Figure out what the columns will be, other than id/age/gender
    colnames = [field for div in self.divisions for field in div[1]]
    colnames = set(colnames)
    if 'Age' in colnames:
      colnames.remove('Age')
    if 'Gender' in colnames:
      colnames.remove('Gender')
    #Create the header string
    tablehead = 'Place,Time,Lap times,Name,Bib ID,Gender,Age'
    for colname in colnames:
      tablehead += ','+colname
    tablehead += '\n'
    #Keep track of the places
    allplace = 1
    divplace = [1 for div in self.divisions]
    divresults = ['\n'+div[0]+'\n'+tablehead for div in self.divisions]
    #go through the data from fastest time to slowest
    if self.offset >= 0:
      adj_ids = ['' for i in range(self.offset)]
      adj_ids.extend(self.rawtimes['ids'])
      adj_times = list(self.rawtimes['times'])
    elif self.offset < 0:
      adj_times = ['' for i in range(-self.offset)]
      adj_times.extend(self.rawtimes['times'])
      adj_ids = list(self.rawtimes['ids'])
    laptimesdic = defaultdict(list)
    #We do a run through all of the times and group lap times
    for (tag,time) in sorted(zip(adj_ids,adj_times), key=lambda entry: entry[1]):
      if tag and time and tag != self.junkid:
        d1 = re.match(r'((?P<days>\d+) days, )?(?P<hours>\d+):'r'(?P<minutes>\d+):(?P<seconds>\d+)',time).groupdict(0) #convert txt time to dict
        laptimesdic[tag].append(datetime.timedelta(**dict(( (key, int(value)) for key, value in d1.items() )))) #convert dict time to datetime, and store
    #Each value of laptimesdic is a list, sorted in order from fastest time (1st lap) to longest time (last lap).
    #Go through and compute the lap times.
    laptimesdic2 = defaultdict(list)
    for tag,times in laptimesdic.iteritems():
      #First put the total race time
      if len(laptimesdic[tag]) == self.numlaps:
        laptimesdic2[tag] = [str(laptimesdic[tag][-1])]
      else:
        laptimesdic2[tag] = ['<>']
      #And now the first lap
      laptimesdic2[tag].append(str(laptimesdic[tag][0]))
      #And now the subsequent laps
      laptimesdic2[tag].extend([str(laptimesdic[tag][ii+1] - laptimesdic[tag][ii]) for ii in range(len(laptimesdic[tag])-1)])
    #Now run through the data one more time and print the results.
    with open(os.sep.join([self.path, self.path+'_'+self.timestr+'_alltimes.csv']),'w') as fout:
      fout.write(tablehead)
      for (tag,times) in sorted(laptimesdic2.items(), key=lambda entry: entry[1][0]):
        age = self.timing[tag]['Age']
        gen = self.timing[tag]['Gender']
        #Our table entry will be the same for both full results and divisionals, except for the place.
        #First the total time and first lap
        tableentry = ','+times[0]+',1 - '+times[1]+','+self.timing[tag]['First name']+' '+self.timing[tag]['Last name']+','+tag+','+gen+','+age
        for colname in colnames:
          tableentry += ','+self.timing[tag][colname]
        tableentry+='\n'
        #And now the lap times
        for ii in range(2,len(times)):
          tableentry += ',,'+str(ii)+' - '+times[ii]+',,,,'
          for colname in colnames:
            tableentry += ','
          tableentry+='\n'
        if times[0] != '<>':
          fout.write(str(allplace)+tableentry)
        else:
          fout.write('<>'+tableentry)
        allplace += 1
        #and the appropriate divisional result
        try:
          age = int(age)
        except ValueError:
          age = ''
        #Now we go through the divisions
        for (divindx,div) in enumerate(self.divisions):
          #First check age.
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
            divplace[divindx]+=1
    #Now write out the divisional results
    with open(os.sep.join([self.path, self.path+'_'+self.timestr+'_divtimes.csv']),'w') as fout:
      for i,divresult in enumerate(divresults):
        if divplace[i] > 1:
          fout.write(divresult)
    return
  
  # End timing window --------------------------------------------------------------------------

if __name__ == '__main__':
  pytimer = PyTimer()
  gtk.main()
