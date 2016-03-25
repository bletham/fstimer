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
'''Handling of the window where rankings are defined'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import fstimer.gui
from fstimer.gui.GtkStockButton import GtkStockButton
from fstimer.gui.util_classes import MsgDialog

class RankingsWin(Gtk.Window):
    '''Handling of the window where rankings are defined'''

    def __init__(self, rankings, back_clicked_cb, next_clicked_cb, parent):
        '''Creates divisions window'''
        super(RankingsWin, self).__init__(Gtk.WindowType.TOPLEVEL)
        self.rankings = rankings
        self.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title('fsTimer - Rankings')
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(20)
        self.set_size_request(600, 400)
        self.connect('delete_event', lambda b, jnk_unused: self.hide())
        # top label
        top_label = Gtk.Label('Use the checkbox to enable/disable sub ranking per category\nUse expression field to give the python code producing the value on which the ranking will be performed')
        # Create a treeview and add columns
        self.rankingview = Gtk.TreeView()
        # Make the model, a liststore with columns str, bool, str
        self.rankingmodel = Gtk.ListStore(str, bool, str)
        for ranking in rankings:
            self.rankingmodel.append(ranking)
        self.rankingview.set_model(self.rankingmodel)
        selection = self.rankingview.get_selection()
        # Add following columns to the treeview :
        # ranking name | use_divs | python code
        ranking_renderer = Gtk.CellRendererText()
        ranking_renderer.set_property("editable", True)
        ranking_renderer.connect("edited", self.ranking_edit)
        column = Gtk.TreeViewColumn('Ranking', ranking_renderer, text=0)
        self.rankingview.append_column(column)
        toggle_renderer = Gtk.CellRendererToggle()
        toggle_renderer.connect("toggled", self.toggle_edit)
        column = Gtk.TreeViewColumn('Use Divs', toggle_renderer, active=1)
        self.rankingview.append_column(column)
        code_renderer = Gtk.CellRendererText()
        code_renderer.set_property("editable", True)
        code_renderer.connect("edited", self.code_edit)
        column = Gtk.TreeViewColumn('Python Code', code_renderer, text=2)
        self.rankingview.append_column(column)
        # Create scrolled window, in an alignment
        rankingsw = Gtk.ScrolledWindow()
        rankingsw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        rankingsw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        rankingsw.add(self.rankingview)
        rankingalgn = Gtk.Alignment.new(0, 0, 1, 1)
        rankingalgn.add(rankingsw)
        # Now we put the buttons on the side.
        vbox2 = Gtk.VBox(False, 10)
        btnREMOVE = GtkStockButton(Gtk.STOCK_REMOVE,"Remove")
        btnREMOVE.connect('clicked', self.ranking_remove, selection)
        vbox2.pack_start(btnREMOVE, False, False, 0)
        btnNEW = GtkStockButton(Gtk.STOCK_NEW,"New")
        btnNEW.connect('clicked', self.ranking_new, selection)
        vbox2.pack_start(btnNEW, False, False, 0)
        btnUP = GtkStockButton(Gtk.STOCK_GO_UP,"Up")
        btnUP.connect('clicked', self.ranking_up, selection)
        vbox2.pack_start(btnUP, False, False, 0)
        btnDOWN = GtkStockButton(Gtk.STOCK_GO_DOWN,"Down")
        btnDOWN.connect('clicked', self.ranking_down, selection)
        vbox2.pack_start(btnDOWN, False, False, 0)
        # And an hbox for the fields and the buttons
        hbox4 = Gtk.HBox(False, 0)
        hbox4.pack_start(rankingalgn, True, True, 10)
        hbox4.pack_start(vbox2, False, False, 0)
        # Add an hbox with 3 buttons
        hbox3 = Gtk.HBox(False, 0)
        btnCANCEL = GtkStockButton(Gtk.STOCK_CANCEL,"Cancel")
        btnCANCEL.connect('clicked', lambda btn: self.hide())
        alignCANCEL = Gtk.Alignment.new(0, 0, 0, 0)
        alignCANCEL.add(btnCANCEL)
        btnBACK = GtkStockButton(Gtk.STOCK_GO_BACK,"Back")
        btnBACK.connect('clicked', back_clicked_cb)
        btnNEXT = GtkStockButton(Gtk.STOCK_GO_FORWARD,"Forward")
        btnNEXT.connect('clicked', next_clicked_cb, None)
        # Populate
        hbox3.pack_start(alignCANCEL, True, True, 0)
        hbox3.pack_start(btnBACK, False, False, 2)
        hbox3.pack_start(btnNEXT, False, False, 0)
        vbox = Gtk.VBox(False, 0)
        vbox.pack_start(top_label, False, False, 0)
        vbox.pack_start(hbox4, True, True, 0)
        vbox.pack_start(hbox3, False, False, 10)
        self.add(vbox)
        self.show_all()

    def ranking_remove(self, jnk_unused, selection):
        '''handles a click on REMOVE button'''
        treeiter1 = selection.get_selected()[1]
        if treeiter1:
            row = self.rankingmodel.get_path(treeiter1)
            row = row[0]
            self.rankingmodel.remove(treeiter1)
            self.rankings.pop(row)
            selection.select_path((row, ))
        return

    def ranking_new(self, jnk_unused, selection):
        '''handles a click on NEW button'''
        # create new name
        name = 'new ranking'
        i = 1
        while name in [r[0] for r in self.rankings]:
            name = 'new ranking%d' % i
            i = i + 1
        # append new line with default content
        self.rankings.append((name, True, 'entry[1]'))
        self.rankingmodel.append((name, True, 'entry[1]'))
        return

    def ranking_up(self, jnk_unused, selection):
        '''Handled click on the UP button'''
        model, treeiter1 = selection.get_selected()
        if treeiter1:
            row = self.rankingmodel.get_path(treeiter1)
            row = row[0]
            if row > 0:
                #this isn't the bottom item, so we can move it up.
                treeiter2 = model.get_iter(row-1)
                self.rankingmodel.swap(treeiter1, treeiter2)
                self.rankings[row], self.rankings[row-1] = self.rankings[row-1], self.rankings[row]
        return

    def ranking_down(self, jnk_unused, selection):
        '''Handled click on the DOWN button'''
        model, treeiter1 = selection.get_selected()
        if treeiter1:
            row = self.rankingmodel.get_path(treeiter1)
            row = row[0]
            if row < len(self.rankings)-1:
                #this isn't the bottom item, so we can move it down.
                treeiter2 = model.get_iter(row+1)
                self.rankingmodel.swap(treeiter1, treeiter2)
                self.rankings[row], self.rankings[row+1] = self.rankings[row+1], self.rankings[row]
        return

    def ranking_edit(self, widget, path, text):
        '''handles a change of a ranking name'''
        ipath = int(path)
        if text != self.rankings[ipath][0]:
            if text not in [r[0] for r in self.rankings]:
                self.rankingmodel[path][0] = text
                oldranking = self.rankings[ipath]
                self.rankings[ipath] = (text, oldranking[1], oldranking[2])
            else:
                md = MsgDialog(self, 'error', 'OK', 'Error!', 'Ranking name "%s" is already used!' % text)
                md.run()
                md.destroy()
        return

    def toggle_edit(self, widget, path):
        '''handles a change of the use divs of a ranking'''
        ipath = int(path)
        oldranking = self.rankings[ipath]
        self.rankingmodel[path][1] = not oldranking[1]
        self.rankings[ipath] = (oldranking[0], not oldranking[1], oldranking[2])
        return
    
    def code_edit(self, widget, path, text):
        '''handles a change of the ranking code'''
        # ToDo : check code validity
        ipath = int(path)
        oldranking = self.rankings[ipath]
        self.rankingmodel[path][2] = text
        self.rankings[ipath] = (oldranking[0], oldranking[1], text)
        return