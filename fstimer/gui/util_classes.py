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
'''Convenience classes for the PyGTK -> PyGObject transition'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os

icon_files = {'new': 'actions/document-new-symbolic.svg',
              'close': 'actions/window-close-symbolic.svg',
              'ok': 'emblems/emblem-ok-symbolic.svg',
              'remove': 'actions/list-remove-symbolic.svg',
              'add': 'actions/list-add-symbolic.svg',
              'up': 'actions/go-up-symbolic.svg',
              'down': 'actions/go-down-symbolic.svg',
              'edit': 'apps/text-editor-symbolic.svg',
              'copy': 'actions/edit-copy-symbolic.svg',
              'back': 'actions/go-previous-symbolic.svg',
              'forward': 'actions/go-next-symbolic.svg',
              'open': 'actions/folder-open-symbolic.svg',
              'clear': 'actions/edit-clear-symbolic.svg',
              'save': 'actions/document-save-symbolic.svg',
              'clock': 'actions/document-open-recent-symbolic.svg',
              'information': 'status/dialog-information-symbolic.svg',
              'error': 'status/dialog-error-symbolic.svg',
              'question': 'status/dialog-question-symbolic.svg',
              'warning': 'status/dialog-warning-symbolic.svg',
              'help': 'actions/help-faq-symbolic.svg',
              'about': 'actions/help-about-symbolic.svg',
              }

dialog_buttons = {'ok': ('ok', 'OK', Gtk.ResponseType.OK),
                  'cancel': ('close', 'Cancel', Gtk.ResponseType.CANCEL),
                  'yes': ('ok', 'Yes', Gtk.ResponseType.YES),
                  'no': ('close', 'No', Gtk.ResponseType.NO),
                  }


class GtkStockButton(Gtk.Button):
    
    def __init__(self, icon_name, label_text):
        #Init a regular Gtk.Button
        Gtk.Button.__init__(self)
        #Add the icon and the label.
        fname = os.path.join('fstimer/data/adwaita_icons', icon_files[icon_name])
        btnIcon = Gtk.Image.new_from_file(fname)
        btnLabel = Gtk.Label(label_text+' ')
        #pack 'em into an HBox
        btnHbox = Gtk.HBox(False, 0)
        btnHbox.pack_start(btnIcon, False, False, 0)
        btnHbox.pack_start(btnLabel, True, True, 0)
        self.add(btnHbox)
        return


class MsgDialog(Gtk.Dialog):
    
    def __init__(self, parent, icon_name, buttons, title, text):
        super(MsgDialog, self).__init__(title, parent, Gtk.DialogFlags.MODAL)
        btn_list = []
        for i, btn_name in enumerate(buttons):
            icon, label, signal = dialog_buttons[btn_name]
            btn = GtkStockButton(icon, label)
            btn.connect('clicked', self.click_response, signal)
            btn_list.append(btn)
        self.set_border_width(5)
        self.set_default_size(400, 50)
        #Load in the icon
        fname = os.path.join('fstimer/data/adwaita_icons', icon_files[icon_name])
        msg_icon = Gtk.Image.new_from_file(fname)
        label = Gtk.Label(label=text)
        #And pack
        hbox = Gtk.HBox(False, 0)
        hbox.pack_start(msg_icon, False, False,10)
        hbox.pack_start(label, False, False,10)
        vbox = Gtk.VBox(False, 0)
        vbox.pack_start(hbox, True, True, 15)
        # Pack in all of the buttons
        hbox_btns = Gtk.HBox(False, 0)
        align = Gtk.Alignment.new(1, 0, 1, 0)
        hbox_btns.pack_start(align, True, True, 0)
        for btn in btn_list:
            hbox_btns.pack_start(btn, False, False, 5)
        vbox.pack_start(hbox_btns, False, False, 0)
        self.get_content_area().add(vbox)
        self.show_all()
    
    def click_response(self, w, signal):
        self.response(signal)


class MenuItemIcon(Gtk.MenuItem):
    
    def __init__(self, icon_name, text, cb, *args):
        super(MenuItemIcon, self).__init__()
        hbox = Gtk.HBox(False, 0)
        fname = os.path.join('fstimer/data/adwaita_icons', icon_files[icon_name])
        msg_icon = Gtk.Image.new_from_file(fname)
        hbox.pack_start(msg_icon, False, False, 0)
        hbox.pack_start(Gtk.Label(label=text), False, False, 5)
        hbox.pack_start(Gtk.Alignment.new(1, 0, 1, 0), True, True, 0)
        self.add(hbox)
        self.connect('activate', cb, *args)