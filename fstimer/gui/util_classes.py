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

class MsgDialog(Gtk.Dialog):
    
    def __init__(self, parent, msg_type, buttons, title, text):
        if buttons == 'YES_NO':
            btn_tpl = (Gtk.STOCK_YES, Gtk.ResponseType.YES, Gtk.STOCK_NO, Gtk.ResponseType.NO)
        elif buttons == 'OK_CANCEL':
            btn_tpl = (Gtk.STOCK_OK, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        elif buttons == 'OK':
            btn_tpl = (Gtk.STOCK_OK, Gtk.ResponseType.OK)
        Gtk.Dialog.__init__(self, title, parent, Gtk.DialogFlags.MODAL, btn_tpl)
        self.set_border_width(5)
        self.set_default_size(400, 50)
        #Load in the icon
        icon_theme = Gtk.IconTheme.get_default() 
        pixbuf = Gtk.IconTheme.load_icon(icon_theme, "dialog-"+msg_type, 48, 0) #msg_type is error, info, question, warning, authentication
        label = Gtk.Label(text)
        #And pack
        hbox = Gtk.HBox(False, 0)
        hbox.pack_start(Gtk.Image.new_from_pixbuf(pixbuf), False, False,10)
        hbox.pack_start(label, False, False,10)
        vbox = Gtk.VBox(False, 0)
        vbox.pack_start(hbox, True, True, 15)
        self.get_content_area().add(vbox)
        self.show_all()