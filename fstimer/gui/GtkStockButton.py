#GtkStockButton - a class that reproduces the deprecated stock buttons
#in GTK3.
#Copyright 2015 Ben Letham

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

'''See github.com/sebp/PyGObject-Tutorial/blob/master/source/stock.txt
for a list of valid values for iconName.
This class reproduces the stock buttons from Gtk3, while avoiding the
"The property GtkButton:use-stock is deprecated" warnings.
Example use:
stockNew = GtkStockButton(Gtk.STOCK_NEW,'New')
'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class GtkStockButton(Gtk.Button):
    
    def __init__(self, iconName, labelText):
        #Init a regular Gtk.Button
        Gtk.Button.__init__(self)
        #Add the icon and the label.
        btnIcon = Gtk.Image.new_from_icon_name(iconName, Gtk.IconSize.SMALL_TOOLBAR)
        btnLabel = Gtk.Label(labelText+' ')
        #pack 'em into an HBox
        btnHbox = Gtk.HBox(False, 0)
        btnHbox.pack_start(btnIcon, False, False, 0)
        btnHbox.pack_start(btnLabel, True, True, 0)
        self.add(btnHbox)
        return