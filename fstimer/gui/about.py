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
'''Handles the about window of the application'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
import os

class AboutWin(Gtk.AboutDialog):
    '''Handles the about window of the application'''

    def __init__(self, parent):
        '''Creates the about window'''
        super(AboutWin, self).__init__()
        self.set_transient_for(parent)
        self.set_modal(True)
        fname = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '../data/icon.png'))
        self.set_logo(GdkPixbuf.Pixbuf.new_from_file(fname))
        self.set_program_name('fsTimer')
        self.set_version('0.6')
        self.set_copyright("""Copyright 2012-16 Ben Letham\
        \nThis program comes with ABSOLUTELY NO WARRANTY; for details see license.\
        \nThis is free software, and you are welcome to redistribute it under certain conditions; see license for details""")
        self.set_comments('free, open source software for race timing.\nhttp://fstimer.org')
        self.set_wrap_license(False)
        fname_c = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '../../COPYING'))
        with open(fname_c, 'r') as fin:
            gpl = fin.read()
        self.set_license(gpl)
        self.set_authors(['Ben Letham',
                          'Sebastien Ponce',
                          'Testing by Stewart Hamblin'])
        self.run()
        self.destroy()
