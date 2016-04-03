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

    def __init__(self, rankings, divisions, printfields, back_clicked_cb, next_clicked_cb, parent, edit):
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
        top_label = Gtk.Label('Select which field the results will be ranked by.\nYou can use any one of the results fields defined on the previous window.')
        self.fieldslist = list(printfields.keys())
        try:
            self.indx = self.fieldslist.index(self.rankings['Overall'])
        except ValueError:
            self.indx = 0
        #overall_align = Gtk.Alignment.new(0, 0, 0, 0)
        #overall_align.add(Gtk.Label('Rank overall results by: '))
        ov_hbox = Gtk.HBox(False, 5)
        ov_hbox.pack_start(Gtk.Label('Rank overall results by:'), False, False, 0)
        # Prep the combobox
        combobox = Gtk.ComboBoxText()
        for field in self.fieldslist:
            combobox.append_text(field)
        combobox.set_active(self.indx)
        combobox.connect('changed', self.overall_edit)
        ov_hbox.pack_start(combobox, False, False, 0)
        apply_btn = Gtk.Button('Apply to divisions')
        apply_btn.connect('clicked', self.apply_to_divs)
        ov_hbox.pack_start(apply_btn, False, False, 5)
        # Create a treeview and add columns
        self.rankingview = Gtk.TreeView()
        # Make the model, a liststore with columns str, str
        self.rankingmodel = Gtk.ListStore(str, str)
        for div in divisions:
            indx_div = self.fieldslist.index(self.rankings[div[0]])
            self.rankingmodel.append([div[0], self.fieldslist[indx_div]])
        self.rankingview.set_model(self.rankingmodel)
        selection = self.rankingview.get_selection()
        # Add following columns to the treeview :
        # Division | Ranking field
        ranking_renderer = Gtk.CellRendererText()
        ranking_renderer.set_property("editable", False)
        column = Gtk.TreeViewColumn('Division', ranking_renderer, text=0)
        self.rankingview.append_column(column)
        #Prepare the combobox liststore
        liststore_fields = Gtk.ListStore(str)
        for field in self.fieldslist:
            liststore_fields.append([field])
        combo_renderer = Gtk.CellRendererCombo()
        combo_renderer.set_property("editable", True)
        combo_renderer.set_property("model", liststore_fields)
        combo_renderer.set_property("text-column", 0)
        combo_renderer.set_property("has-entry", False)
        combo_renderer.connect("edited", self.ranking_edit)
        column = Gtk.TreeViewColumn('Rank by:', combo_renderer, text=1)
        self.rankingview.append_column(column)
        # Create scrolled window, in an alignment
        rankingsw = Gtk.ScrolledWindow()
        rankingsw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        rankingsw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        rankingsw.add(self.rankingview)
        rankingalgn = Gtk.Alignment.new(0, 0, 1, 1)
        rankingalgn.add(rankingsw)
        # And an hbox for the fields and the buttons
        hbox4 = Gtk.HBox(False, 0)
        hbox4.pack_start(rankingalgn, True, True, 10)
        # Add an hbox with 3 buttons
        hbox3 = Gtk.HBox(False, 0)
        btnCANCEL = GtkStockButton(Gtk.STOCK_CANCEL,"Cancel")
        btnCANCEL.connect('clicked', lambda btn: self.hide())
        alignCANCEL = Gtk.Alignment.new(0, 0, 0, 0)
        alignCANCEL.add(btnCANCEL)
        btnBACK = GtkStockButton(Gtk.STOCK_GO_BACK,"Back")
        btnBACK.connect('clicked', back_clicked_cb)
        btnNEXT = GtkStockButton(Gtk.STOCK_GO_FORWARD,"Forward")
        btnNEXT.connect('clicked', next_clicked_cb, edit)
        # Populate
        hbox3.pack_start(alignCANCEL, True, True, 0)
        hbox3.pack_start(btnBACK, False, False, 2)
        hbox3.pack_start(btnNEXT, False, False, 0)
        vbox = Gtk.VBox(False, 0)
        vbox.pack_start(top_label, False, False, 0)
        vbox.pack_start(ov_hbox, False, False, 15)
        vbox.pack_start(hbox4, True, True, 0)
        vbox.pack_start(hbox3, False, False, 10)
        self.add(vbox)
        self.show_all()

    def ranking_edit(self, widget, path, text):
        '''handles a change of a ranking field'''
        treeiter = self.rankingmodel.get_iter(path)
        div = self.rankingmodel.get_value(treeiter, 0)
        self.rankingmodel[path][1] = text
        self.rankings[div] = text
        return
    
    def overall_edit(self, widget):
        '''handles a change of the overall ranking field'''
        idx = widget.get_active()
        self.rankings['Overall'] = self.fieldslist[idx]
        return
    
    def apply_to_divs(self, widget):
        '''sets divs to the overall setting on button click'''
        for div in self.rankings:
            if div != 'Overall':
                self.rankings[div] = str(self.rankings['Overall'])
        for i in range(len(self.rankings)-1):
            itr = self.rankingmodel.get_iter(i)
            self.rankingmodel.set_value(itr, 1, self.rankings['Overall'])