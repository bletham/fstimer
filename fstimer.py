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
import os,re,time,json,datetime,sys,csv,webbrowser,string
import fstimer.gui.intro, fstimer.gui.newproject, fstimer.gui.definefields, fstimer.gui.definefamilyreset
from collections import defaultdict

class PyTimer:
  
  def delete_event(*args):
    gtk.main_quit()
  
  def __init__(self):
    self.bgcolor = fstimer.gui.bgcolor
    self.introwin = fstimer.gui.intro.IntroWin(self.load_project,
                                               self.create_project)
    
  #Here we have selected a project with combobox from intro window. We define path, load the registration settings, and goto rootwin
  def load_project(self,jnk,combobox,projectlist):
    self.path = projectlist[combobox.get_active()]+'/'
    with open(self.path+self.path[:-1]+'.reg','rb') as fin:
      regdata = json.load(fin)
    self.fields = regdata['fields']
    self.fieldsdic = regdata['fieldsdic']
    self.clear_for_fam = regdata['clear_for_fam']
    self.divisions = regdata['divisions']
    self.introwin.hide()
    self.root_window()

  def create_project(self, jnk):
    '''creates a new project'''
    self.newprojectwin = fstimer.gui.newproject.NewProjectWin(self.define_fields,
                                                              self.introwin)

  def define_fields(self, path):
    '''Handled the definition of fields when creating a new project'''
    self.path = path
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
    self.definefieldswin.hide()
    self.gen_win1_4()
    return
    
  def gen_win1_4(self):
    #Create a new window and define handlers
    self.win1_4 = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.win1_4.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
    self.win1_4.set_transient_for(self.introwin)
    self.win1_4.set_modal(True)
    self.win1_4.set_title('fsTimer - New project')
    self.win1_4.set_position(gtk.WIN_POS_CENTER)
    self.win1_4.set_border_width(20)
    self.win1_4.set_size_request(800, 600)
    self.win1_4.connect('delete_event',lambda b,jnk: self.win1_4.hide())
    ##Now create the vbox.
    vbox1 = gtk.VBox(False,10)
    self.win1_4.add(vbox1)
    ##Now add the text.
    label2_0 = gtk.Label("Specify the divisions for reporting divisional places.\nPress 'Forward' to continue with the default settings, or make edits below.")
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
    #Make the liststore, with columns:
    #name | min age | max age | (... all other combobox fields...)
    #To do this we first count the number of combobox fields
    ncbfields = len([field for field in self.fields if self.fieldsdic[field]['type'] == 'combobox'])
    self.divmodel = gtk.ListStore(*[str for i in range(ncbfields+3)])
    #We will put the liststore in a treeview
    self.divview = gtk.TreeView()
    #Add each of the columns
    Columns = {}
    Columns[1] = gtk.TreeViewColumn('Division name',gtk.CellRendererText(),text=0)
    self.divview.append_column(Columns[1])
    Columns[2] = gtk.TreeViewColumn('Min age',gtk.CellRendererText(),text=1)
    self.divview.append_column(Columns[2])
    Columns[3] = gtk.TreeViewColumn('Max age',gtk.CellRendererText(),text=2)
    self.divview.append_column(Columns[3])
    #And now the additional columns
    textcount = 3
    for field in self.fields:
      if self.fieldsdic[field]['type'] == 'combobox':
        Columns[field] = gtk.TreeViewColumn(field,gtk.CellRendererText(),text=textcount)
        textcount += 1
        self.divview.append_column(Columns[field])
    #Now we populate the model with the default fields
    divmodelrows = {}
    for ii,div in enumerate(self.divisions):
      #Add in the divisional name
      divmodelrows[ii] = [div[0]]
      #Next the two age columns
      if 'Age' in  div[1]:
        divmodelrows[ii].extend([str(div[1]['Age'][0]),str(div[1]['Age'][1])])
      else:
        divmodelrows[ii].extend(['',''])
      #And then all other columns
      for field in self.fields:
        if self.fieldsdic[field]['type'] == 'combobox':
          if field in div[1]:
            divmodelrows[ii].append(div[1][field])
          else:
            divmodelrows[ii].append('')
      #All done! Add this row in.
      self.divmodel.append(divmodelrows[ii])
    #Done there.
    self.divview.set_model(self.divmodel)
    selection = self.divview.get_selection()
    #And put it in a scrolled window, in an alignment
    divsw = gtk.ScrolledWindow()
    divsw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
    divsw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    divsw.add(self.divview)
    divalgn = gtk.Alignment(0,0,1,1)
    divalgn.add(divsw)
    #Now we put the buttons on the side.
    vbox2 = gtk.VBox(False,10)
    btnUP = gtk.Button(stock=gtk.STOCK_GO_UP)
    btnUP.connect('clicked',self.div_up,selection)
    vbox2.pack_start(btnUP,False,False,0)
    btnDOWN = gtk.Button(stock=gtk.STOCK_GO_DOWN)
    btnDOWN.connect('clicked',self.div_down,selection)
    vbox2.pack_start(btnDOWN,False,False,0)
    btnEDIT = gtk.Button(stock=gtk.STOCK_EDIT)
    btnEDIT.connect('clicked',self.div_edit,selection)
    vbox2.pack_start(btnEDIT,False,False,0)
    btnREMOVE = gtk.Button(stock=gtk.STOCK_REMOVE)
    btnREMOVE.connect('clicked',self.div_remove,selection)
    vbox2.pack_start(btnREMOVE,False,False,0)
    btnNEW = gtk.Button(stock=gtk.STOCK_NEW)
    btnNEW.connect('clicked',self.div_new,('',{}),None)
    vbox2.pack_start(btnNEW,False,False,0)
    #And an hbox for the fields and the buttons
    hbox4 = gtk.HBox(False,0)
    hbox4.pack_start(divalgn,True,True,10)
    hbox4.pack_start(vbox2,False,False,0)
    ##And an hbox with 3 buttons
    hbox3 = gtk.HBox(False,0)
    btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
    btnCANCEL.connect('clicked',lambda btn: self.win1_4.hide())
    alignCANCEL = gtk.Alignment(0,0,0,0)
    alignCANCEL.add(btnCANCEL)
    btnBACK = gtk.Button(stock=gtk.STOCK_GO_BACK)
    btnBACK.connect('clicked',self.win1_4_back)
    btnNEXT = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
    btnNEXT.connect('clicked',self.win1_4_next)
    ##And populate
    hbox3.pack_start(alignCANCEL,True,True,0)
    hbox3.pack_start(btnBACK,False,False,2)
    hbox3.pack_start(btnNEXT,False,False,0)
    vbox1.pack_start(label2_0,False,False,0)
    #vbox1.pack_start(label2_1,False,False,0)
    #vbox1.pack_start(hbox1,False,False,0)
    #vbox1.pack_start(hbox2,False,False,0)
    vbox1.pack_start(hbox4,True,True,0)
    vbox1.pack_start(hbox3,False,False,10)
    self.win1_4.show_all()    
    return
  
  def win1_4_back(self,jnk):
    self.win1_4.hide()
    self.definefieldswin.show_all()
    return
  
  def div_up(self,jnk,selection):
    model,treeiter1 = selection.get_selected()
    if treeiter1:
      row = self.divmodel.get_path(treeiter1)
      row = row[0]
      if row > 0:
        #this isn't the bottom item, so we can move it up.
        treeiter2 = model.get_iter(row-1)
        self.divmodel.swap(treeiter1,treeiter2)
        self.divisions[row],self.divisions[row-1] = self.divisions[row-1],self.divisions[row]
    return
        
  def div_down(self,jnk,selection):
    model,treeiter1 = selection.get_selected()
    if treeiter1:
      row = self.divmodel.get_path(treeiter1)
      row = row[0]
      if row < len(self.divisions)-1:
        #this isn't the bottom item, so we can move it down.
        treeiter2 = model.get_iter(row+1)
        self.divmodel.swap(treeiter1,treeiter2)
        self.divisions[row],self.divisions[row+1] = self.divisions[row+1],self.divisions[row]
    return
        
  def div_edit(self,jnk,selection):
    model,treeiter1 = selection.get_selected()
    if treeiter1:
      row = self.divmodel.get_path(treeiter1)
      row = row[0]
      self.div_new(None,self.divisions[row],treeiter1)
    return
  
  def div_new(self,jnk,divtupl,treeiter):
    self.winnewdiv = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.winnewdiv.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
    self.winnewdiv.set_transient_for(self.win1_4)
    self.winnewdiv.set_modal(True)
    self.winnewdiv.set_title('fsTimer - New project')
    self.winnewdiv.set_position(gtk.WIN_POS_CENTER)
    self.winnewdiv.set_border_width(20)
    self.winnewdiv.connect('delete_event',lambda b,jnk: self.winnewdiv.hide())
    #Prepare for packing.
    vbox = gtk.VBox(False,10)
    windescr = gtk.Label('Use the checkboxes to select which fields to use to define this division,\nand then select the corresponding value to be used for this division.')
    vbox.pack_start(windescr,False,False,0)
    HBoxes = {}
    CheckButtons = {}
    ComboBoxes = {}
    #Process the input
    divnamein = divtupl[0]
    divdic = divtupl[1]
    #First name of the divisional.
    divnamelbl = gtk.Label('Division name:')
    divnameentry = gtk.Entry(max=80)
    divnameentry.set_width_chars(40)
    divnameentry.set_text(divnamein) #set to initial value
    HBoxes[1] = gtk.HBox(False,10) #an int as key so it will never collide with a user field
    HBoxes[1].pack_start(divnamelbl,False,False,0)
    HBoxes[1].pack_start(divnameentry,False,False,0)
    vbox.pack_start(HBoxes[1],False,False,0)
    #Then do Age
    CheckButtons['Age'] = gtk.CheckButton(label='Age:')
    if 'Age' in divdic:
      #if minage, then also maxage - we always have both.
      CheckButtons['Age'].set_active(True)
      minageadj = gtk.Adjustment(value=divdic['Age'][0],lower=0,upper=120,step_incr=1)
      maxageadj = gtk.Adjustment(value=divdic['Age'][1],lower=0,upper=120,step_incr=1)
    else:
      minageadj = gtk.Adjustment(value=0,lower=0,upper=120,step_incr=1)
      maxageadj = gtk.Adjustment(value=120,lower=0,upper=120,step_incr=1)
    minagelbl = gtk.Label('Min age (inclusive):')
    minagebtn = gtk.SpinButton(minageadj,digits=0,climb_rate=0)
    maxagelbl = gtk.Label('Max age (inclusive):')    
    maxagebtn = gtk.SpinButton(maxageadj,digits=0,climb_rate=0)
    #Make an hbox of it.
    HBoxes['Age'] = gtk.HBox(False,10)
    HBoxes['Age'].pack_start(CheckButtons['Age'],False,False,0)
    HBoxes['Age'].pack_start(minagelbl,False,False,0)
    HBoxes['Age'].pack_start(minagebtn,False,False,0)
    HBoxes['Age'].pack_start(maxagelbl,False,False,0)
    HBoxes['Age'].pack_start(maxagebtn,False,False,0)
    vbox.pack_start(HBoxes['Age'],False,False,0)
    #And now all other combobox fields
    for field in self.fields:
      if self.fieldsdic[field]['type'] == 'combobox':
        #Add it.
        CheckButtons[field] = gtk.CheckButton(label=field+':')
        ComboBoxes[field] = gtk.combo_box_new_text()
        for option in self.fieldsdic[field]['options']:
          ComboBoxes[field].append_text(option)
          if field in divdic and divdic[field]:
            CheckButtons[field].set_active(True) #the box is checked
            ComboBoxes[field].set_active(self.fieldsdic[field]['options'].index(divdic[field])) #set to initial value
        #Put it in an HBox
        HBoxes[field] = gtk.HBox(False,10)
        HBoxes[field].pack_start(CheckButtons[field],False,False,0)
        HBoxes[field].pack_start(ComboBoxes[field],False,False,0)
        vbox.pack_start(HBoxes[field],False,False,0)
    #On to the bottom buttons
    btnOK = gtk.Button(stock=gtk.STOCK_OK)
    btnOK.connect('clicked',self.winnewdivOK,treeiter,CheckButtons,ComboBoxes,minagebtn,maxagebtn,divnameentry)
    btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
    btnCANCEL.connect('clicked',lambda b: self.winnewdiv.hide())
    cancel_algn = gtk.Alignment(0,0,0,0)
    cancel_algn.add(btnCANCEL)
    hbox3 = gtk.HBox(False,10)
    hbox3.pack_start(cancel_algn,True,True,0)
    hbox3.pack_start(btnOK,False,False,0)
    vbox.pack_start(hbox3,False,False,0)
    self.winnewdiv.add(vbox)
    self.winnewdiv.show_all()
    return
    
  def div_remove(self,jnk,selection):
    model,treeiter1 = selection.get_selected()
    if treeiter1:
      row = self.divmodel.get_path(treeiter1)
      row = row[0]
      self.divmodel.remove(treeiter1)
      self.divisions.pop(row)
      selection.select_path((row,))
    return
    
  def winnewdivOK(self,jnk,treeiter,CheckButtons,ComboBoxes,minagebtn,maxagebtn,divnameentry):
    #First get the division name
    div = (divnameentry.get_text(),{}) #this will be the new entry in self.divisions
    #Now get age, if included.
    if CheckButtons['Age'].get_active():
      minage = minagebtn.get_value_as_int()
      maxage = maxagebtn.get_value_as_int()
      div[1]['Age'] = (minage,maxage)
    #And now go through the other fields.
    for field,btn in CheckButtons.items():
      if field != 'Age' and btn.get_active() and ComboBoxes[field].get_active()>-1:
        div[1][field] = self.fieldsdic[field]['options'][ComboBoxes[field].get_active()]
    if treeiter:
      #we are replacing a division
      row = self.divmodel.get_path(treeiter)
      row = row[0]
      self.divisions[row] = div #replace the old division with the new one in self.divisions
      #And now update the divmodel
      self.divmodel.set_value(treeiter,0,div[0])
      if 'Age' in div[1]:
        self.divmodel.set_value(treeiter,1,div[1]['Age'][0])
        self.divmodel.set_value(treeiter,2,div[1]['Age'][1])
      else:
        self.divmodel.set_value(treeiter,1,'')
        self.divmodel.set_value(treeiter,2,'')
      colcount = 3
      for field in self.fields:
        if self.fieldsdic[field]['type'] == 'combobox':
          if field in div[1]:
            self.divmodel.set_value(treeiter,colcount,div[1][field])
          else:
            self.divmodel.set_value(treeiter,colcount,'')
          colcount+=1
    else:
      #no treeiter- this was a new entry.
      #Add it to self.divisions
      self.divisions.append(div)
      #Add in the divisional name
      divmodelrow = [div[0]]
      #Next the two age columns
      if 'Age' in  div[1]:
        divmodelrow.extend([str(div[1]['Age'][0]),str(div[1]['Age'][1])])
      else:
        divmodelrow.extend(['',''])
      #And then all other columns
      for field in self.fields:
        if self.fieldsdic[field]['type'] == 'combobox':
          if field in div[1]:
            divmodelrow.append(div[1][field])
          else:
            divmodelrow.append('')
      #All done! Add this row in.
      self.divmodel.append(divmodelrow)
    self.winnewdiv.hide()
    return
    
  def win1_4_next(self,jnk):
    os.system('mkdir '+self.path[:-1])
    regdata = {}
    regdata['fields'] = self.fields
    regdata['fieldsdic'] = self.fieldsdic
    regdata['clear_for_fam'] = self.clear_for_fam
    regdata['divisions'] = self.divisions
    with open(self.path+self.path[:-1]+'.reg','wb') as fout:
      json.dump(regdata,fout)
    md = gtk.MessageDialog(self.win1_4,gtk.DIALOG_MODAL,gtk.MESSAGE_INFO,gtk.BUTTONS_OK,'Project '+self.path[:-1]+' successfully created!')
    md.run()
    md.destroy()
    self.win1_4.hide()
    self.introwin.hide()
    self.root_window()
    return
      
  # End project name window --------------------------------------------------------------------------  
  # Root window --------------------------------------------------------------------------    
  ##This defines the root window with choices for the tasks
  def root_window(self):
    #Set up the window
    self.rootwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.rootwin.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
    self.rootwin.set_icon_from_file('fstimer_icon.png')
    self.rootwin.set_title('fsTimer - '+self.path[:-1])
    self.rootwin.set_position(gtk.WIN_POS_CENTER)
    self.rootwin.connect('delete_event',self.delete_event)
    self.rootwin.set_border_width(0)
    #Generate the menubar
    mb = gtk.MenuBar()
    helpmenu = gtk.Menu()
    helpm = gtk.MenuItem('Help')
    helpm.set_submenu(helpmenu)
    menuhelp = gtk.ImageMenuItem(gtk.STOCK_HELP)
    menuhelp.connect('activate',lambda jnk: webbrowser.open('documentation/documentation_sec2.htm'))
    helpmenu.append(menuhelp)
    menuabout = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
    menuabout.connect('activate',self.show_about)
    helpmenu.append(menuabout)
    mb.append(helpm)
    ### Frame
    rootframe = gtk.Frame(label='al')
    self.rootframe_label = gtk.Label('')
    self.rootframe_label.set_markup('<b>fsTimer project '+self.path[:-1]+'</b>')
    rootframe.set_label_widget(self.rootframe_label)
    rootframe.set_border_width(20)
    #And now fill the frame with a table
    roottable = gtk.Table(4,2,False)
    roottable.set_row_spacings(20)
    roottable.set_col_spacings(20)
    roottable.set_border_width(10)
    #And internal buttons
    rootbtnPREREG = gtk.Button('Preregister')
    rootbtnPREREG.connect('clicked',self.importprereg_window)
    rootlabelPREREG = gtk.Label('')
    rootlabelPREREG.set_alignment(0,0.5)
    rootlabelPREREG.set_markup('Prepare pre-registration file.')
    rootbtnREG = gtk.Button('Register')
    rootbtnREG.connect('clicked',self.prereg_window)
    rootlabelREG = gtk.Label('')
    rootlabelREG.set_alignment(0,0.5)
    rootlabelREG.set_markup('Register racer information and assign ID numbers.')
    rootbtnCOMP = gtk.Button('Compile')
    rootbtnCOMP.connect('clicked',self.compreg_window)
    rootlabelCOMP = gtk.Label('')
    rootlabelCOMP.set_alignment(0,0.5)
    rootlabelCOMP.set_markup('Compile registrations from multiple computers.')
    rootbtnTIME = gtk.Button('Time')
    rootbtnTIME.connect('clicked',self.gen_pretimewin)
    rootlabelTIME = gtk.Label('')
    rootlabelTIME.set_alignment(0,0.5)
    rootlabelTIME.set_markup('Record race times on the day of the race.')
    roottable.attach(rootbtnPREREG,0,1,0,1)
    roottable.attach(rootlabelPREREG,1,2,0,1)    
    roottable.attach(rootbtnREG,0,1,1,2)
    roottable.attach(rootlabelREG,1,2,1,2)
    roottable.attach(rootbtnCOMP,0,1,2,3)
    roottable.attach(rootlabelCOMP,1,2,2,3)
    roottable.attach(rootbtnTIME,0,1,3,4)
    roottable.attach(rootlabelTIME,1,2,3,4)
    rootframe.add(roottable)
    ### Buttons
    roothbox = gtk.HBox(True,0)
    rootbtnQUIT = gtk.Button(stock=gtk.STOCK_QUIT)
    rootbtnQUIT.connect('clicked',self.delete_event)
    roothbox.pack_start(rootbtnQUIT,False,False,5)
    #Vbox
    rootvbox = gtk.VBox(False,0)
    btnhalign = gtk.Alignment(1, 0, 0, 0)
    btnhalign.add(roothbox)
    rootvbox.pack_start(mb,False,False,0)
    rootvbox.pack_start(rootframe,True,True,0)
    rootvbox.pack_start(btnhalign,False,False,5)
    self.rootwin.add(rootvbox)
    self.rootwin.show_all()
    return
    
  # End root window --------------------------------------------------------------------------
  # About window --------------------------------------------------------------------------
  #This defines the about window.
  def show_about(self,jnk):
    about = gtk.AboutDialog()
    about.set_logo(gtk.gdk.pixbuf_new_from_file("fstimer_icon.png"))
    about.set_program_name('fsTimer')
    about.set_version('0.4')
    about.set_copyright('Copyright 2012-14 Ben Letham\nThis program comes with ABSOLUTELY NO WARRANTY; for details see license.\nThis is free software, and you are welcome to redistribute it under certain conditions; see license for details')
    about.set_comments('free, open source software for race timing.')
    about.set_website('http://fstimer.org')
    about.set_wrap_license(True)
    with open('COPYING','r') as fin:
      gpl = fin.read()
    about.set_license(gpl)
    about.set_authors(['Ben Letham','Testing by Stewart Hamblin'])
    about.run()
    about.destroy()
    return
  
  # End about window --------------------------------------------------------------------------
  # Import pre-registration window --------------------------------------------------------------------------
  #With this window we import pre-registration from a csv
  def importprereg_window(self,jnk):
    #Define the window
    self.importpreregwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.importpreregwin.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
    self.importpreregwin.set_icon_from_file('fstimer_icon.png')
    self.importpreregwin.set_title('fsTimer - '+self.path[:-1])
    self.importpreregwin.set_position(gtk.WIN_POS_CENTER)
    self.importpreregwin.connect('delete_event',lambda b,jnk: self.importpreregwin.hide())
    self.importpreregwin.set_border_width(10)
    self.importpreregwin.set_size_request(600,400)
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
    textalgn = gtk.Alignment(0,0,1,1)
    textalgn.add(textsw)
    hbox2 = gtk.HBox(False,5)
    btnFILE.connect('clicked',self.preregimp,textbuffer)
    btn_algn = gtk.Alignment(1,0,1,0)
    hbox2.pack_start(btnFILE,False,False,0)
    hbox2.pack_start(btn_algn,True,True,0)
    ## buttons
    btnOK = gtk.Button(stock=gtk.STOCK_OK)
    btnOK.connect('clicked',lambda b: self.importpreregwin.hide())
    cancel_algn = gtk.Alignment(0,0,1,0)
    hbox3 = gtk.HBox(False,10)
    hbox3.pack_start(cancel_algn,True,True,0)
    hbox3.pack_start(btnOK,False,False,0)
    vbox = gtk.VBox(False,0)
    vbox.pack_start(label1,False,False,5)
    vbox.pack_start(hbox2,False,True,5)
    vbox.pack_start(textalgn,True,True,5)
    vbox.pack_start(hbox3,False,False,0)
    self.importpreregwin.add(vbox)
    self.importpreregwin.show_all()
    return
    
  #Here we have selected to use a pre-reg file. We do this with a filechooser.
  def preregimp(self,jnk,textbuffer):
    chooser = gtk.FileChooserDialog(title='Select pre-registration csv',action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))
    ffilter = gtk.FileFilter()
    ffilter.set_name('csv files')
    ffilter.add_pattern('*.csv')
    chooser.add_filter(ffilter)
    self.pwd = os.getcwd()
    chooser.set_current_folder(self.pwd+'/'+self.path)
    response = chooser.run()
    if response == gtk.RESPONSE_OK:
      filename = chooser.get_filename()
      textbuffer.set_text('Loading '+os.path.basename(filename)+'...\n')
      try:
        fin = csv.DictReader(open(filename,'r'))
        csvreg = []
        for row in fin:
          csvreg.append(row)
        csv_fields = csvreg[0].keys()
        try:
          textbuffer.create_tag("blue",  foreground = "blue")
          textbuffer.create_tag("red",  foreground = "red")
        except TypeError:
          pass
        printstr = 'Found csv fields: '
        if csv_fields:
          for field in csv_fields:
            printstr+=field+', '
          printstr = printstr[:-2]
        printstr+='\n'
        iter1 = textbuffer.get_end_iter()
        textbuffer.insert(iter1,printstr)
        iter1 = textbuffer.get_iter_at_line(1)
        iter2 = textbuffer.get_iter_at_line_offset(1,17)
        textbuffer.apply_tag_by_name("blue", iter1, iter2)
        printstr = 'Using csv fields: '
        fields_use = [field for field in csv_fields if field in self.fields]
        if fields_use:
          for field in fields_use:
            printstr+=field+', '
          printstr = printstr[:-2]
        printstr+='\n'
        iter1 = textbuffer.get_end_iter()
        textbuffer.insert(iter1,printstr)
        iter1 = textbuffer.get_iter_at_line(2)
        iter2 = textbuffer.get_iter_at_line_offset(2,17)
        textbuffer.apply_tag_by_name("blue", iter1, iter2)
        printstr = 'Ignoring csv fields: '
        fields_ignore = [field for field in csv_fields if field not in self.fields]
        if fields_ignore:
          for field in fields_ignore:
            printstr+=field+', '
          printstr = printstr[:-2]
        printstr+='\n'
        iter1 = textbuffer.get_end_iter()
        textbuffer.insert(iter1,printstr)
        iter1 = textbuffer.get_iter_at_line(3)
        iter2 = textbuffer.get_iter_at_line_offset(3,20)
        textbuffer.apply_tag_by_name("red", iter1, iter2)
        printstr = 'Did not find: '
        fields_notuse = [field for field in self.fields if field not in csv_fields]
        if fields_notuse:
          for field in fields_notuse:
            printstr+=field+', '
          printstr = printstr[:-2]
        printstr+='\n'
        iter1 = textbuffer.get_end_iter()
        textbuffer.insert(iter1,printstr)
        iter1 = textbuffer.get_iter_at_line(4)
        iter2 = textbuffer.get_iter_at_line_offset(4,13)
        textbuffer.apply_tag_by_name("red", iter1, iter2)
        iter1 = textbuffer.get_end_iter()
        textbuffer.insert(iter1,'Importing registration data...\n')
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
                    optstr+='"'+opt+'", '
                  optstr += 'and blank'
                  iter1 = textbuffer.get_end_iter()
                  textbuffer.insert(iter1,'Error in csv row '+str(row+1)+'! Found value "'+reg[field]+'" in field "'+field+'". Not a valid value!\nValid values (case sensitive) are: '+optstr+'.\nNothing was imported. Correct the error and try again.')
                  iter1 = textbuffer.get_iter_at_line(6)
                  iter2 = textbuffer.get_end_iter()
                  textbuffer.apply_tag_by_name("red", iter1, iter2)
              tmpdict[field] = str(reg[field])
            preregdata.append(tmpdict.copy())
            row += 1
        if breakloop ==0:
          with open(self.path+self.path[:-1]+'_registration_prereg.json','wb') as fout:
            json.dump(preregdata,fout)
          iter1 = textbuffer.get_end_iter()
          textbuffer.insert(iter1,'Success! Imported pre-registration saved to '+self.path[:-1]+'_registration_prereg.json\nFinished!')
          iter1 = textbuffer.get_iter_at_line(6)
          iter2 = textbuffer.get_end_iter()
          textbuffer.apply_tag_by_name("blue", iter1, iter2)
      except (IOError,IndexError):
        iter1 = textbuffer.get_end_iter()
        try:
          textbuffer.create_tag("red",  foreground = "red")
        except TypeError:
          pass
        textbuffer.insert(iter1,'Error! Could not open file, or no data found in file. Nothing was imported, try again.')
        iter1 = textbuffer.get_iter_at_line(1)
        iter2 = textbuffer.get_end_iter()
        textbuffer.apply_tag_by_name("red", iter1, iter2)
    chooser.destroy()
    return
  
  # End import pre-registration window --------------------------------------------------------------------------  
  # Pre-registration window --------------------------------------------------------------------------
  #With this window we set the computers registration ID, and optionally choose a pre-registration json
  def prereg_window(self,jnk):
    #Define the window
    self.preregwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.preregwin.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
    self.preregwin.set_icon_from_file('fstimer_icon.png')
    self.preregwin.set_title('fsTimer - '+self.path[:-1])
    self.preregwin.set_position(gtk.WIN_POS_CENTER)
    self.preregwin.connect('delete_event',lambda b,jnk: self.preregwin.hide())
    self.preregwin.set_border_width(10)
    # Start with some intro text.
    prereglabel1 = gtk.Label('Give a unique number to each computer used for registration.\nSelect a pre-registration file, if available.')
    #Continue to the spinner.
    preregtable = gtk.Table(3,2,False)
    preregtable.set_row_spacings(5)
    preregtable.set_col_spacings(5)
    preregtable.set_border_width(10)    
    regid = gtk.Adjustment(value=1,lower=1,upper=99,step_incr=1)
    self.regid_btn = gtk.SpinButton(regid,digits=0,climb_rate=0)
    preregtable.attach(self.regid_btn,0,1,0,1)
    preregtable.attach(gtk.Label("This computer's registration number"),1,2,0,1)
    preregbtnFILE = gtk.Button('Select pre-registration')
    preregbtnFILE.connect('clicked',self.preregsel)
    preregtable.attach(preregbtnFILE,0,1,2,3)
    self.preregfilelabel = gtk.Label('')
    self.preregfilelabel.set_markup('<span color="blue">No pre-registration selected.</span>')
    preregtable.attach(self.preregfilelabel,1,2,2,3)
    ## buttons
    prereghbox = gtk.HBox(True,0)
    preregbtnOK = gtk.Button(stock=gtk.STOCK_OK)
    preregbtnOK.connect('clicked',self.reg_window)
    preregbtnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
    preregbtnCANCEL.connect('clicked',lambda b: self.preregwin.hide())
    prereghbox.pack_start(preregbtnOK,False,False,5)
    prereghbox.pack_start(preregbtnCANCEL,False,False,5)
    #Vbox
    preregvbox = gtk.VBox(False,0)
    preregbtnhalign = gtk.Alignment(1, 0, 0, 0)
    preregbtnhalign.add(prereghbox)
    preregvbox.pack_start(prereglabel1,False,False,5)
    preregvbox.pack_start(preregtable,False,False,5)
    preregvbox.pack_start(preregbtnhalign,False,False,5)
    self.preregwin.add(preregvbox)
    self.preregwin.show_all()
    return
    
  #Here we have selected to use a pre-reg file. We do this with a filechooser.
  def preregsel(self,jnk):
    chooser = gtk.FileChooserDialog(title='Select pre-registration file',action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))
    ffilter = gtk.FileFilter()
    ffilter.set_name('Registration files')
    ffilter.add_pattern('*_registration_*.json')
    chooser.add_filter(ffilter)
    self.pwd = os.getcwd()
    chooser.set_current_folder(self.pwd+'/'+self.path)
    response = chooser.run()
    if response == gtk.RESPONSE_OK:
      filename = chooser.get_filename()
      try:
        with open(filename,'rb') as fin:
          self.prereg = json.load(fin)
        self.preregfilelabel.set_markup('<span color="blue">Pre-registration '+os.path.basename(filename)+' loaded.</span>')
      except (IOError, ValueError):
        self.preregfilelabel.set_markup('<span color="red">ERROR! Failed to load '+os.path.basename(filename)+'.</span>')
    chooser.destroy()
    return
  
  # End pre-registration window --------------------------------------------------------------------------  
  # Registration window --------------------------------------------------------------------------
  #With this window we show the registration table.
  def reg_window(self,jnk):
    #This is the important information to take from the pre-registration window.
    self.regid = self.regid_btn.get_value_as_int()
    self.preregwin.hide()
    #First we define the registration model.
    #We will setup a liststore that is wrapped in a treemodelfilter that is wrapped in a treemodelsort that is put in a treeview that is put in a scrolled window. Eesh.
    self.regmodel = gtk.ListStore(*[str for field in self.fields])
    self.modelfilter = self.regmodel.filter_new()
    self.modelfiltersorted = gtk.TreeModelSort(self.modelfilter)
    self.treeview = gtk.TreeView()
    #Now we define each column in the treeview. We take these from self.fields, defined in __init__
    for (colid,field) in enumerate(self.fields):
      column = gtk.TreeViewColumn(field,gtk.CellRendererText(),text=colid)
      column.set_sort_column_id(colid)
      self.treeview.append_column(column)
    self.lastnamecol = self.fields.index('Last name')
    #Now we populate the model with the pre-registration info, if there is any.
    #self.prereg is a list of dictionaries.
    try:
      for reg in self.prereg:
        self.regmodel.append([reg[field] for field in self.fields])
    except AttributeError:
      self.prereg = [] #We start with a blank prereg if none was loaded, or it did not have the correct fields. 
    self.searchstr = '' #This is the string that we filter based on.
    self.modelfilter.set_visible_func(self.visible_filter)
    self.treeview.set_model(self.modelfiltersorted)
    self.treeview.set_enable_search(False)
    #Now let us actually build the window
    self.regwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.regwin.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
    self.regwin.set_icon_from_file('fstimer_icon.png')
    self.regwin.set_title('fsTimer - '+self.path[:-1])
    self.regwin.set_position(gtk.WIN_POS_CENTER)
    self.regwin.connect('delete_event',lambda b,jnk: self.reg_ok(jnk))
    self.regwin.set_border_width(10)
    self.regwin.set_size_request(850, 450)
    #Now the filter entrybox
    filterbox = gtk.HBox(False,8)
    filterbox.pack_start(gtk.Label('Filter by last name:'),False,False,0)
    self.filterentry = gtk.Entry(max=40)
    self.filterentry.connect('changed',self.filter_apply)
    self.filterbtnCLEAR = gtk.Button(stock=gtk.STOCK_CLEAR)
    self.filterbtnCLEAR.connect('clicked',self.filter_clear)
    self.filterbtnCLEAR.set_sensitive(False)
    filterbox.pack_start(self.filterentry,False,False,0)
    filterbox.pack_start(self.filterbtnCLEAR,False,False,0)
    #Now the scrolled window that contains the treeview
    regsw = gtk.ScrolledWindow()
    regsw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
    regsw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    regsw.add(self.treeview)
    #And a message that says if we have saved or not.
    self.regstatus = gtk.Label('')
    #Some boxes for all the stuff on the left
    regvbox1 = gtk.VBox(False,8)
    regvbox1.pack_start(filterbox,False,False,0)
    regvbox1.pack_start(regsw,True,True,0)
    regvbox1.pack_start(self.regstatus,False,False,0)
    vbox1align = gtk.Alignment(0,0,1,1)
    vbox1align.add(regvbox1)
    #And boxes/table for the buttons on the right
    regtable = gtk.Table(2,1,False)
    regtable.set_row_spacings(5)
    regtable.set_col_spacings(5)
    regtable.set_border_width(5)
    btnEDIT = gtk.Button(stock=gtk.STOCK_EDIT)
    btnEDIT.connect('clicked',self.edit_reg)
    btnREMOVE = gtk.Button(stock=gtk.STOCK_REMOVE)
    btnREMOVE.connect('clicked',self.rm_reg)
    btnFAM = gtk.Button('Add family')
    btnFAM.connect('clicked',self.fam_reg)
    btnNEW = gtk.Button(stock=gtk.STOCK_NEW)
    btnNEW.connect('clicked',self.new_reg)
    btnSAVE = gtk.Button(stock=gtk.STOCK_SAVE)
    btnSAVE.connect('clicked',self.save_reg)
    btnOK = gtk.Button('Done')
    btnOK.connect('clicked',self.reg_ok)
    vsubbox = gtk.VBox(False,8)
    vsubbox.pack_start(btnSAVE,False,False,0)
    vsubbox.pack_start(btnOK,False,False,0)
    regvspacer = gtk.Alignment(1, 1, 0, 0)
    regvspacer.add(vsubbox)
    regtable.attach(regvspacer,0,1,1,2)
    regvbox2 = gtk.VBox(False,8)
    regvbox2.pack_start(btnEDIT,False,False,0)
    regvbox2.pack_start(btnREMOVE,False,False,0)
    regvbox2.pack_start(btnFAM,False,False,0)
    regvbox2.pack_start(btnNEW,False,False,0)
    regvbalign = gtk.Alignment(1, 0, 0, 0)
    regvbalign.add(regvbox2)
    regtable.attach(regvbalign,0,1,0,1)
    #Now we pack everything together
    reghbox = gtk.HBox(False,8)
    reghbox.pack_start(vbox1align,True,True,0)
    reghbox.pack_start(regtable,False,False,0)
    self.regwin.add(reghbox)
    #And show.
    self.regwin.show_all()
    return
    
  #Here we have modified the contents of the filter box. 
  #We will set self.searchstr to the current entrybox contents and refilter.
  def filter_apply(self,jnk):
    self.searchstr = self.filterentry.get_text()
    self.filterbtnCLEAR.set_sensitive(True)
    self.modelfilter.refilter()
    return
    
  #Here we have cleared the filter box. Set self.searchstr to blank and refilter.
  def filter_clear(self,jnk):
    self.searchstr = ''
    self.filterentry.set_text('')
    self.filterbtnCLEAR.set_sensitive(False)
    self.modelfilter.refilter()
    return
    
  #This is the function we use to filter. It checks if self.searchstr is contained in column self.lastnamecol, case insensitive.
  def visible_filter(self,model,titer):
    if self.searchstr:
      if not model.get_value(titer,self.lastnamecol):
        return False
      elif self.searchstr.lower() in model.get_value(titer,self.lastnamecol).lower():
        return True
      else:
        return False
    else:
      return True
  
  #Here we have clicked for a new registration
  #Create the editreg window with a None treeiter and clear initial values.
  def new_reg(self,jnk):
    self.gen_editregwin(None,None,None)
    return
  
  #Here we have chosen to remove a registration entry.
  #Throw up an 'are you sure' dialog box, and delete if yes.
  def rm_reg(self,jnk):
    selection = self.treeview.get_selection()
    model,treeiter = selection.get_selected()
    #if nothing is selected, do nothing.
    if treeiter:
      rmreg_dialog = gtk.MessageDialog(self.regwin,gtk.DIALOG_MODAL,gtk.MESSAGE_QUESTION,gtk.BUTTONS_YES_NO,'Are you sure you want to delete this entry?\nThis cannot be undone.')
      rmreg_dialog.set_title('Woah!')
      rmreg_dialog.set_default_response(gtk.RESPONSE_NO)
      response = rmreg_dialog.run()
      rmreg_dialog.destroy()
      if response == gtk.RESPONSE_YES:
        #We convert the treeiter from sorted to filter to model, and remove
        self.regmodel.remove(self.modelfilter.convert_iter_to_child_iter(self.modelfiltersorted.convert_iter_to_child_iter(None,treeiter)))
        self.regstatus.set_markup('') #The latest stuff has no longer been saved.
    return
  
  #Here we have clicked to save the current registration information. We do a json dump of self.prereg.
  def save_reg(self,jnk):
    with open(self.path+self.path[:-1]+'_registration_'+str(self.regid)+'.json','wb') as fout:
      json.dump(self.prereg,fout)
    self.regstatus.set_markup('<span color="blue">Registration saved to '+self.path+self.path[:-1]+'_registration_'+str(self.regid)+'.json</span>')
    return
  
  #We have clicked 'OK' on the registration window.
  #Throw up a 'do you want to save' dialog, and close the window.
  def reg_ok(self,jnk):
    okreg_dialog = gtk.MessageDialog(self.regwin,gtk.DIALOG_MODAL,gtk.MESSAGE_QUESTION,gtk.BUTTONS_YES_NO,'Do you want to save before finishing?\nUnsaved data will be lost.')
    okreg_dialog.set_title('Save?')
    okreg_dialog.set_default_response(gtk.RESPONSE_YES)
    response = okreg_dialog.run()
    okreg_dialog.destroy()
    if response == gtk.RESPONSE_YES:
      self.save_reg(None) #this will save.
    self.regwin.hide()
    #Clear the file setting from pre-reg, in case pre-reg is re-run without selecting a file
    del self.prereg
    return
  
  #Here we have clicked 'edit' on the registration window.
  def edit_reg(self,jnk):
    selection = self.treeview.get_selection()
    model,treeiter = selection.get_selected()
    #if no selection, do nothing.
    if treeiter:
      #Grab the current information.
      current_info = {}
      for (colid,field) in enumerate(self.fields):
        current_info[field] = self.modelfiltersorted.get_value(treeiter,colid)
      ##Find where this is in self.prereg.
      preregiter = self.prereg.index(current_info)
      #Generate the window
      self.gen_editregwin(treeiter,preregiter,current_info)
    return
    
  #Here we have clicked 'add family' on the registration window.
  #We construct current_info the same as in self.edit_reg, but pass None instead of treeiter.
  def fam_reg(self,jnk):
    selection = self.treeview.get_selection()
    model,treeiter = selection.get_selected()
    #if no selection, do nothing.
    if treeiter:
      #Grab the current information.
      current_info = {}
      for (colid,field) in enumerate(self.fields):
        current_info[field] = self.modelfiltersorted.get_value(treeiter,colid)
      #Drop some info
      for field in self.clear_for_fam:
        current_info[field] = ''
      #Generate the window
      self.gen_editregwin(None,None,current_info)
    return
  
  # End registration window --------------------------------------------------------------------------  
  # Edit registration window --------------------------------------------------------------------------
  #This window is used either to create a new entry in the registration table or to modify an existing entry.
  def gen_editregwin(self,treeiter,preregiter,current_info):
    #Convert the treeiter from the treemodelsort to the liststore.
    if treeiter:
      treeiter = self.modelfilter.convert_iter_to_child_iter(self.modelfiltersorted.convert_iter_to_child_iter(None,treeiter))
    #Define the window
    self.editreg_win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.editreg_win.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
    self.editreg_win.set_title('Registration entry')
    self.editreg_win.set_transient_for(self.regwin)
    self.editreg_win.set_modal(True)
    self.editreg_win.set_position(gtk.WIN_POS_CENTER)
    self.editreg_win.connect('delete_event',lambda b,jnk: self.editreg_win.hide())
    self.editreg_win.set_border_width(10)
    #Create all of the buttons, and fill in current_info if available.
    self.editregfields = {}
    for field in self.fields:
      #Determine which type of entry is appropriate, and create it and fill it.
      #Entrybox
      if self.fieldsdic[field]['type'] == 'entrybox':
        self.editregfields[field] = gtk.Entry(max=self.fieldsdic[field]['max'])
        if current_info:
          self.editregfields[field].set_text(current_info[field])
      #Spinbutton
      #elif self.fieldsdic[field]['type'] == 'spinbutton':
      #  self.editregfields[field] = gtk.SpinButton(gtk.Adjustment(value=self.fieldsdic[field]['lower'], lower = self.fieldsdic[field]['lower'], upper = self.fieldsdic[field]['upper'],step_incr=1),digits=0,climb_rate=0)
      #  if current_info:
      #    try:
      #      self.editregfields[field].set_value(int(current_info[field]))
      #    except ValueError:
      #      pass #this catches if current_inf[field]='', and the int('') throws a ValueError.
      #Combobox
      elif self.fieldsdic[field]['type'] == 'combobox':
        self.editregfields[field] = gtk.combo_box_new_text()
        self.editregfields[field].append_text('')
        for val in self.fieldsdic[field]['options']:
          self.editregfields[field].append_text(val)
        if current_info:
          try:
            indx = self.fieldsdic[field]['options'].index(current_info[field])
            self.editregfields[field].set_active(indx+1)
          except ValueError:
            self.editregfields[field].set_active(0) #this catches if current_inf[field] is not a valid value. It is probably blank. Otherwise this is an issue, but we will force it blank.
        else:
          self.editregfields[field].set_active(0)
    #Set up the vbox
    editregvbox = gtk.VBox(False,8)
    #We will make a smaller hbox for each of the fields.
    hboxes = {}
    for field in self.fields:
      hboxes[field] = gtk.HBox(False,15)
      hboxes[field].pack_start(gtk.Label(field+':'),False,False,0) #Pack the label
      hboxes[field].pack_start(self.editregfields[field],False,False,0) #Pack the button/entry/..
      editregvbox.pack_start(hboxes[field],False,False,0) #Pack this hbox into the big vbox.
    #An hbox for the buttons
    editreghbox = gtk.HBox(False,8)
    editregbtnOK = gtk.Button(stock=gtk.STOCK_OK)
    editregbtnOK.connect('clicked',self.editentry,treeiter,preregiter)
    editregbtnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
    editregbtnCANCEL.connect('clicked',lambda b: self.editreg_win.hide())
    editreghbox.pack_start(editregbtnOK,False,False,5)
    editreghbox.pack_start(editregbtnCANCEL,False,False,5)
    #Pack and show
    editregvbox.pack_start(editreghbox,False,False,5)
    self.editreg_win.add(editregvbox)
    self.editreg_win.show_all()
    return
  
  #Here we have clicked 'OK' from the edit registration window. 
  #This will read out the inputted information, and write the changes to the treemodel.
  def editentry(self,jnk,treeiter,preregiter):
    #First we go through each field and grab the new value.
    new_vals = {}
    for field in self.fields:
      #Entrybox
      if self.fieldsdic[field]['type'] == 'entrybox':
        new_vals[field] = self.editregfields[field].get_text()
      #Spinbutton
      #elif self.fieldsdic[field]['type'] == 'spinbutton':
      #  #If it is zero, we will leave it blank.
      #  idfill = self.editregfields[field].get_value_as_int()
      #  if idfill == 0:
      #    idfill = ''
      #  else:
      #    if field == 'ID':
      #      #We pad ID to self.idlen digits
      #      idfill = str(idfill).zfill(self.idlen)
      #    else:
      #      idfill = str(idfill)
      #  new_vals[field] = idfill
      #Combobox
      elif self.fieldsdic[field]['type'] == 'combobox':
        indx = self.editregfields[field].get_active()
        if indx == 0:
          new_vals[field] = ''
        else:
          new_vals[field] = self.fieldsdic[field]['options'][indx-1]
    ##This code will open a dialog box to warn if an ID was not assigned.
    #if not new_vals['ID']:
      #checkid_dialog = gtk.MessageDialog(self.regwin,gtk.DIALOG_MODAL,gtk.MESSAGE_INFO,gtk.BUTTONS_YES_NO,'You did not assign an ID.\nAre you sure you want this?')
      #checkid_dialog.set_title('Woah!')
      #response = checkid_dialog.run()
      #checkid_dialog.destroy()
      #if response == gtk.RESPONSE_NO:
        #return
    ##Now we replace or append in the treemodel and in our prereg list-of-dictionaries
    if treeiter:
      for (colid,field) in enumerate(self.fields):
        self.regmodel.set_value(treeiter,colid,new_vals[field])
      self.prereg[preregiter] = new_vals
    else:
      self.regmodel.append([new_vals[field] for field in self.fields])
      self.prereg.append(new_vals)
    #The saved status is unsaved
    self.regstatus.set_markup('')
    #Filter results by this last name
    self.filterentry.set_text(new_vals['Last name'])
    #we're done
    self.editreg_win.hide()
    return
  
  # End edit registration window --------------------------------------------------------------------------  
  # Compile registration window --------------------------------------------------------------------------
  #Here we merge registration files and create the timing dictionary.
  def compreg_window(self,jnk):
    #Create the window
    self.compregwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.compregwin.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
    self.compregwin.set_icon_from_file('fstimer_icon.png')
    self.compregwin.set_title('fsTimer - '+self.path[:-1])
    self.compregwin.set_position(gtk.WIN_POS_CENTER)
    self.compregwin.connect('delete_event', lambda b,jnk: self.compregwin.hide())
    self.compregwin.set_border_width(10)
    self.compregwin.set_size_request(600, 450)
    #We will use a liststore to hold the filenames of the registrations to be merged,
    #and put the liststore in a scrolledwindow
    compregsw = gtk.ScrolledWindow()
    compregsw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
    compregsw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.reglist = gtk.ListStore(str)
    self.comptreeview = gtk.TreeView()
    rendererText = gtk.CellRendererText()
    column = gtk.TreeViewColumn('Registration files',rendererText,text=0)
    column.set_sort_column_id(0)
    self.comptreeview.append_column(column)
    self.comptreeview.set_model(self.reglist)
    compregsw.add(self.comptreeview)
    #We have text below the window to explain what is happening during merging
    self.comblabel1 = gtk.Label('')
    self.comblabel1.set_alignment(0,0.5)
    self.comblabel2 = gtk.Label('')
    self.comblabel2.set_alignment(0,0.5)
    self.comblabel3 = gtk.Label('')
    self.comblabel3.set_alignment(0,0.5)
    #Pack it all
    regvbox1 = gtk.VBox(False,8)
    regvbox1.pack_start(gtk.Label('Select all of the registration files to merge'),False,False,0)
    regvbox1.pack_start(compregsw,True,True,0)
    regvbox1.pack_start(self.comblabel1,False,False,0)
    regvbox1.pack_start(self.comblabel2,False,False,0)
    regvbox1.pack_start(self.comblabel3,False,False,0)
    vbox1align = gtk.Alignment(0,0,1,1)
    vbox1align.add(regvbox1)
    #The buttons in a table
    regtable = gtk.Table(2,1,False)
    regtable.set_row_spacings(5)
    regtable.set_col_spacings(5)
    regtable.set_border_width(5)
    btnREMOVE = gtk.Button(stock=gtk.STOCK_REMOVE)
    btnREMOVE.connect('clicked',self.rm_compreg)
    btnADD = gtk.Button(stock=gtk.STOCK_ADD)
    btnADD.connect('clicked',self.add_compreg)
    btnMERGE = gtk.Button('Merge')
    btnMERGE.connect('clicked',self.merge_compreg)
    btnOK = gtk.Button('Done')
    btnOK.connect('clicked', lambda jnk: self.compregwin.hide())
    vsubbox = gtk.VBox(False,8)
    vsubbox.pack_start(btnMERGE,False,False,0)
    vsubbox.pack_start(btnOK,False,False,0)
    regvspacer = gtk.Alignment(1, 1, 0, 0)
    regvspacer.add(vsubbox)
    regtable.attach(regvspacer,0,1,1,2)
    regvbox2 = gtk.VBox(False,8)
    regvbox2.pack_start(btnREMOVE,False,False,0)
    regvbox2.pack_start(btnADD,False,False,0)
    regvbalign = gtk.Alignment(1, 0, 0, 0)
    regvbalign.add(regvbox2)
    regtable.attach(regvbalign,0,1,0,1)
    reghbox = gtk.HBox(False,8)
    reghbox.pack_start(vbox1align,True,True,0)
    reghbox.pack_start(regtable,False,False,0)
    #Add and show
    self.compregwin.add(reghbox)
    self.compregwin.show_all()
    return
  
  #Here we have selected to remove a pre-reg file from the list
  def rm_compreg(self,jnk):
    selection = self.comptreeview.get_selection()
    model,comptreeiter = selection.get_selected()
    #if something was selected...
    if comptreeiter:
      model.remove(comptreeiter)
    return
    
  #Here we have selected to add a pre-reg file to the list. We do this with a filechooser.
  def add_compreg(self,jnk):
    chooser = gtk.FileChooserDialog(title='Select registration files',action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_ADD,gtk.RESPONSE_OK))
    chooser.set_select_multiple(True)
    ffilter = gtk.FileFilter()
    ffilter.set_name('Registration files')
    ffilter.add_pattern('*registration_*.json')
    chooser.add_filter(ffilter)
    self.pwd = os.getcwd()
    chooser.set_current_folder(self.pwd+'/'+self.path)
    response = chooser.run()
    if response == gtk.RESPONSE_OK:
      filenames = chooser.get_filenames()
      for filenm in filenames:
        self.reglist.append([filenm])
    chooser.destroy()
    return
  
  #Here we have chosen to merge all of the files in the treeview.
  #Create a list of these filenames, and if it is nonempty, json load them and merge.
  #Also create a timing dictionary, which is a dictionary with IDs as keys.
  #Finally, we check for errors
  def merge_compreg(self,jnk):
    self.regfilelist = []
    #Grab all of the filenames from the liststore
    self.reglist.foreach(lambda model,path,titer: self.regfilelist.append(model.get_value(titer,0)))
    if self.regfilelist:
      #Here we use labels under the scrolledwindow to keep track of the status.
      self.comblabel1.set_markup('<span color="blue">Combining registrations...</span>')
      self.comblabel2.set_markup('')
      self.comblabel3.set_markup('')
      #This will be a list of the merged registrations (each registration is a list of dictionaries)
      self.regmerge = []
      for fname in self.regfilelist:
        with open(fname,'rb') as fin:
          reglist = json.load(fin)
        self.regmerge.extend(reglist)
      #Now remove dups
      self.reg_nodups0 = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in self.regmerge)]
      #Get rid of entries that differ only by the ID. That is, items that were in the pre-reg and had no changes except an ID was assigned in one reg file.
      #we'll do this in O(n^2) time:-(
      self.reg_nodups = []
      for reg in self.reg_nodups0:
        if reg['ID']:
          self.reg_nodups.append(reg)
        else:
          #make sure there isn't an entry with everything else the same, but an ID
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
      #Now form the Timing dictionary, and check for errors.
      self.comblabel2.set_markup('<span color="blue">Checking for errors...</span>')
      self.timedict = {} #the timing dictionary. keys are IDs, values are registration dictionaries
      self.errors = {} #the errors dictionary. keys are IDs, values are a list registration dictionaries with that ID 
      for reg in self.reg_nodups:
        #Any registration without an ID is left out of the timing dictionary
        if reg['ID']:
          #have we already added this ID to the timing dictionary?
          if reg['ID'] in self.timedict.keys():
            #If not, then we need to first add to the list the reg that was already stored in timedict.
            if reg['ID'] not in self.errors.keys():
              self.errors[reg['ID']] = [self.timedict[reg['ID']]]
            self.errors[reg['ID']].append(reg)
          else:
            self.timedict[reg['ID']] = reg
      #If there are errors, we must correct them
      if self.errors:
        self.comblabel2.set_markup('<span color="blue">Checking for errors...</span> <span color="red">Errors found!</span>')
        #Now we make a dialog to view errors...
        self.comperrorswin = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.comperrorswin.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
        self.comperrorswin.set_transient_for(self.compregwin)
        self.comperrorswin.set_modal(True)
        self.comperrorswin.set_title('fsTimer - '+self.path[:-1])
        self.comperrorswin.set_position(gtk.WIN_POS_CENTER)
        self.comperrorswin.connect('delete_event',lambda b,jnk: self.cancel_error(jnk))
        self.comperrorswin.set_border_width(10)
        self.comperrorswin.set_size_request(450, 300)
        #We will make a liststore with all of the overloaded IDs (that is, the keys of self.errors)
        #and put it in a scrolled window
        comperrorsw = gtk.ScrolledWindow()
        comperrorsw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        comperrorsw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.errorlist = gtk.ListStore(str)
        self.errortreeview = gtk.TreeView()
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Overloaded IDs',rendererText,text=0)
        column.set_sort_column_id(0)
        self.errortreeview.append_column(column)
        #add on the IDs from self.errors
        for errorid in self.errors.keys():
          self.errorlist.append([errorid])
        self.errortreeview.set_model(self.errorlist)
        comperrorsw.add(self.errortreeview)
        errvbox1 = gtk.VBox(False,8)
        errvbox1.pack_start(gtk.Label('These IDs were assigned to multiple entries.\nThey will be left unassigned.'),False,False,0)
        errvbox1.pack_start(comperrorsw,True,True,0)
        vbox1align = gtk.Alignment(0,0,1,1)
        vbox1align.add(errvbox1)
        #buttons
        btnVIEW = gtk.Button('View ID entries')
        btnVIEW.connect('clicked',self.view_entries) 
        btnOK = gtk.Button(stock=gtk.STOCK_OK)
        btnOK.connect('clicked', self.ok_error)
        errvbalign = gtk.Alignment(1, 0, 0, 0)
        vbox2 = gtk.VBox(False,10)
        vbox2.pack_start(errvbalign,True,True,0)
        vbox2.pack_start(btnVIEW,False,False,0)
        vbox2.pack_start(btnOK,False,False,0)
        hbox = gtk.HBox(False,10)
        hbox.pack_start(vbox1align,False,False,0)
        hbox.pack_start(vbox2,False,False,0)
        self.comperrorswin.add(hbox)
        self.comperrorswin.show_all()
      else:
        #If no errors, continue on
        self.compreg_noerrors()
    return
  
  #Here we found overloaded IDs while merging, and have chosen to view one.
  #We will load a new window that will list the registration entries overloaded on this ID.
  #We will then give an option to keep one of the registration entries associated with this ID.
  def view_entries(self,jnk):
    selection = self.errortreeview.get_selection()
    model,treeiter = selection.get_selected()
    if treeiter:
      current_id = self.errorlist.get_value(treeiter,0)
      #Define the new window
      self.corerrorswin = gtk.Window(gtk.WINDOW_TOPLEVEL)
      self.corerrorswin.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
      self.corerrorswin.set_transient_for(self.comperrorswin)
      self.corerrorswin.set_modal(True)
      self.corerrorswin.set_title('fsTimer - '+self.path[:-1])
      self.corerrorswin.set_position(gtk.WIN_POS_CENTER)
      self.corerrorswin.connect('delete_event',lambda b,jnk: self.corerrorswin.hide())
      self.corerrorswin.set_border_width(10)
      self.corerrorswin.set_size_request(800, 300)
      #This will be a liststore in a treeview in a scrolled window, as usual
      corerrorsw = gtk.ScrolledWindow()
      corerrorsw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
      corerrorsw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
      self.corerrorlist = gtk.ListStore(*[str for field in self.fields])
      self.corerrortreeview = gtk.TreeView()
      #Now we define each column in the treeview. We take these from self.fields, defined in __init__
      for (colid,field) in enumerate(self.fields):
        column = gtk.TreeViewColumn(field,gtk.CellRendererText(),text=colid)
        column.set_sort_column_id(colid)
        self.corerrortreeview.append_column(column)
      #And add in the info from self.errors
      for reg in self.errors[current_id]:
        self.corerrorlist.append([reg[field] for field in self.fields])
      self.corerrortreeview.set_model(self.corerrorlist)
      corerrorsw.add(self.corerrortreeview)
      errvbox1 = gtk.VBox(False,8)
      errvbox1.pack_start(gtk.Label('These entries share the same ID.\nUse "Keep entry" to associate an entry with the ID.\nOtherwise, press "OK" to continue, no entry will be associated with this ID.'),False,False,0)
      errvbox1.pack_start(corerrorsw,True,True,0)
      vbox1align = gtk.Alignment(0,0,1,1)
      vbox1align.add(errvbox1)
      #Now build a table for the buttons
      errtable = gtk.Table(2,1,False)
      errtable.set_row_spacings(5)
      errtable.set_col_spacings(5)
      errtable.set_border_width(5)
      btnKEEP = gtk.Button('Keep entry')
      btnKEEP.connect('clicked',self.keep_correct,current_id,treeiter)
      btnCANCEL = gtk.Button(stock=gtk.STOCK_OK)
      btnCANCEL.connect('clicked', lambda b: self.corerrorswin.hide())
      vsubbox = gtk.VBox(False,8)
      vsubbox.pack_start(btnCANCEL,False,False,0)
      errvspacer = gtk.Alignment(1, 1, 0, 0)
      errvspacer.add(vsubbox)
      errtable.attach(errvspacer,0,1,1,2)
      errvbox2 = gtk.VBox(False,8)
      errvbox2.pack_start(btnKEEP,False,False,0)
      errvbalign = gtk.Alignment(1, 0, 0, 0)
      errvbalign.add(errvbox2)
      errtable.attach(errvbalign,0,1,0,1)
      errhbox = gtk.HBox(False,8)
      errhbox.pack_start(vbox1align,True,True,0)
      errhbox.pack_start(errtable,False,False,0)
      self.corerrorswin.add(errhbox)
      #And show
      self.corerrorswin.show_all()
    return
  
  #Here we have chosen to keep an entry while correcting an error
  #We replace timingdict with the chosen entry, and remove it from the error list.
  def keep_correct(self,jnk,current_id,treeiter1):
    selection = self.corerrortreeview.get_selection()
    model,treeiter = selection.get_selected()
    if treeiter:
      new_vals = {}
      for (colid,field) in enumerate(self.fields):
        new_vals[field] = model.get_value(treeiter,colid)
      #Replace the timedict entry with the selected entry
      self.timedict[current_id] = new_vals
      #Remove this ID from the errors list
      del self.errors[current_id]
      #And remove it from the error liststore
      self.errorlist.remove(treeiter1)
      #we are now done correcting this error
      self.corerrorswin.hide()
      #if there are no more errors to correct, we move on.
      if not self.errorlist.get_iter_first():
        self.comperrorswin.hide()
        self.compreg_noerrors(True)
    return
    
  #Here we have chosen ok. We continue with the errors.
  #Remove the remaining errors from the timingdict.
  def ok_error(self,jnk):
    for reg in self.errors.keys():
      #these are the remaining errors
      self.timedict.pop(reg)
    self.comperrorswin.hide()
    self.compreg_noerrors(True)
    return

  #Here we no longer have any errors (either we had none to begin with, or we have corrected them all)
  #We write the dictionaries to the disk
  #We also write a csv
  def compreg_noerrors(self,errs=False):
    if errs:
      self.comblabel2.set_markup('<span color="blue">Checking for errors... errors corrected.</span>')
    else:
      self.comblabel2.set_markup('<span color="blue">Checking for errors... no errors found!</span>')
    #Now save things
    with open(self.path+self.path[:-1]+'_registration_compiled.json','wb') as fout:
      json.dump(self.reg_nodups,fout)
    with open(self.path+self.path[:-1]+'_timing_dict.json','wb') as fout:
      json.dump(self.timedict,fout)
    self.comblabel3.set_markup('<span color="blue">Successfully wrote files:\n'+self.path+self.path[:-1]+'_registration_compiled.json\n'+self.path+self.path[:-1]+'_timing_dict.json</span>')
    #And write the compiled registration to csv
    with open(self.path+self.path[:-1]+'_registration.csv','wb') as fout:
      dict_writer = csv.DictWriter(fout,self.fields)
      dict_writer.writer.writerow(self.fields)
      dict_writer.writerows(self.reg_nodups)
    return
    
  # End compile registration window --------------------------------------------------------------------------  
  # Pre-timing window --------------------------------------------------------------------------
  #Here we select a timing dictionary to use
  def gen_pretimewin(self,jnk):
    self.pretimewin = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.pretimewin.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
    self.pretimewin.set_icon_from_file('fstimer_icon.png')
    self.pretimewin.set_title('fsTimer - Project '+self.path[:-1])
    self.pretimewin.set_position(gtk.WIN_POS_CENTER)
    self.pretimewin.connect('delete_event',lambda b,jnk: self.pretimewin.hide())
    self.pretimewin.set_border_width(10)
    # Start with some intro text.
    btnFILE = gtk.Button('Choose file')
    btnFILE.connect('clicked',self.choose_timingdict)
    self.pretimefilelabel = gtk.Label('')
    self.pretimefilelabel.set_markup('<span color="blue">Select a timing dictionary.</span>')
    self.timing = defaultdict(lambda: defaultdict(str))
    entry1 = gtk.Entry(max=6)
    label2 = gtk.Label('Specify a "pass" ID, not assigned to any racer')
    timebtncombobox = gtk.combo_box_new_text()
    timebtnlist = [' ','.','/']
    timebtndescr = ['Spacebar (" ")','Period (".")','Forward slash ("/")']
    for descr in timebtndescr:
      timebtncombobox.append_text(descr)
    timebtncombobox.set_active(0)
    label3 = gtk.Label('Specify the key for marking times. It must not be in any of the IDs.')
    hbox3 = gtk.HBox(False,10)
    hbox3.pack_start(timebtncombobox,False,False,8)
    hbox3.pack_start(label3,False,False,8)
    check_button = gtk.CheckButton(label='Strip leading zeros from IDs? (Probably leave this unchecked)')
    check_button2 = gtk.CheckButton(label='Multiple laps? Specify number if more than one:')
    numlapsadj = gtk.Adjustment(value=2,lower=2,upper=10,step_incr=1)
    numlapsbtn = gtk.SpinButton(numlapsadj,digits=0,climb_rate=0)
    btnCANCEL = gtk.Button(stock=gtk.STOCK_CANCEL)
    btnCANCEL.connect('clicked',lambda b: self.pretimewin.hide())
    pretimebtnOK = gtk.Button(stock=gtk.STOCK_OK)
    pretimebtnOK.connect('clicked',self.gen_timewin,entry1,timebtncombobox,timebtnlist,check_button,check_button2,numlapsbtn)
    btmhbox = gtk.HBox(False,8)
    btmhbox.pack_start(pretimebtnOK,False,False,8)
    btmhbox.pack_start(btnCANCEL,False,False,8)
    btmalign = gtk.Alignment(1, 0, 0, 0)
    btmalign.add(btmhbox)
    hbox = gtk.HBox(False,10)
    hbox.pack_start(btnFILE,False,False,8)
    hbox.pack_start(self.pretimefilelabel,False,False,8)
    hbox2 = gtk.HBox(False,10)
    hbox2.pack_start(entry1,False,False,8)
    hbox2.pack_start(label2,False,False,8)
    hbox4 = gtk.HBox(False,10)
    hbox4.pack_start(check_button2,False,False,8)
    hbox4.pack_start(numlapsbtn,False,False,8)
    vbox = gtk.VBox(False,10)
    vbox.pack_start(hbox,False,False,8)
    vbox.pack_start(hbox2,False,False,8)
    vbox.pack_start(hbox3,False,False,8)
    vbox.pack_start(check_button,False,False,8)
    vbox.pack_start(hbox4,False,False,8)
    vbox.pack_start(btmalign,False,False,8)
    self.pretimewin.add(vbox)
    self.pretimewin.show_all()
    return  
  
  #Here we have chosen to load a timing dictionary
  #We will convert the selected file into a defaultdict
  def choose_timingdict(self,jnk):
    chooser = gtk.FileChooserDialog(title='Choose timing dictionary',action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))
    self.pwd = os.getcwd()
    chooser.set_current_folder(self.pwd+'/'+self.path)
    ffilter = gtk.FileFilter()
    ffilter.set_name('Timing dictionaries')
    ffilter.add_pattern('*_timing_dict.json')
    chooser.add_filter(ffilter)
    response = chooser.run()
    if response == gtk.RESPONSE_OK:
      filename = chooser.get_filename()
      self.timing = defaultdict(lambda: defaultdict(str)) #reset
      try:
        with open(filename,'rb') as fin:
          a = json.load(fin)
        for reg in a.keys():
          self.timing[reg].update(a[reg])
        self.pretimefilelabel.set_markup('<span color="blue">'+os.path.basename(filename)+' loaded.</span>')
      except (IOError, ValueError):
        self.pretimefilelabel.set_markup('<span color="red">ERROR! '+os.path.basename(filename)+' not valid.</span>')
    chooser.destroy()
    return
    
  # End pre-timing window --------------------------------------------------------------------------  
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
    self.timewin.set_title('fsTimer - '+self.path[:-1])
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
    self.t0win.set_title('fsTimer - '+self.path[:-1])
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
    chooser.set_current_folder(self.pwd+'/'+self.path)
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
    with open(self.path+self.path[:-1]+'_'+self.timestr+'_times.json','wb') as fout:
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
        with open(self.path+self.path[:-1]+'_'+self.timestr+'_alltimes.html','w') as fout:
          fout.write(fullresults+tablefoot+htmlfoot)
        with open(self.path+self.path[:-1]+'_'+self.timestr+'_divtimes.html','w') as fout:
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
      with open(self.path+self.path[:-1]+'_'+self.timestr+'_alltimes.csv','w') as fout:
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
      with open(self.path+self.path[:-1]+'_'+self.timestr+'_divtimes.csv','w') as fout:
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
      with open(self.path+self.path[:-1]+'_'+self.timestr+'_alltimes.html','w') as fout:
        fout.write(fullresults+tablefoot+htmlfoot)
      with open(self.path+self.path[:-1]+'_'+self.timestr+'_divtimes.html','w') as fout:
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
    with open(self.path+self.path[:-1]+'_'+self.timestr+'_alltimes.csv','w') as fout:
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
    with open(self.path+self.path[:-1]+'_'+self.timestr+'_divtimes.csv','w') as fout:
      for i,divresult in enumerate(divresults):
        if divplace[i] > 1:
          fout.write(divresult)
    return
  
  # End timing window --------------------------------------------------------------------------

if __name__ == '__main__':
  pytimer = PyTimer()
  gtk.main()
