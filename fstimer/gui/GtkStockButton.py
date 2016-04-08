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

'''This class reproduces the stock buttons from Gtk3, while avoiding the
"The property GtkButton:use-stock is deprecated" warnings.
'''

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