#!/usr/bin/env python3

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

'''Printer class for html files for multi lap races'''

import fstimer.printhtml

class HTMLPrinterLaps(fstimer.printhtml.HTMLPrinter):
    '''Printer class for html files for multi lap races'''

    def __init__(self, fields, categories):
        '''constructor
           @type fields: list
           @param fields: fields of the output
           @type categories: list
           @param categories: existing categories'''
        super(HTMLPrinterLaps, self).__init__(fields, categories)

    def common_entry(self, row):
        '''Returns the common part of the printout of the entry
           of a given runner for scratch or by category results
           @type bibid: string'''
        # first line, as before
        entry = '</td><td>'.join(row)+'</td></tr>\n'
        if 'Lap Times' in self.fields:
            idx_lap = self.fields.index('Lap Times')
            for i in range(1, len(row[idx_lap])):
                entry += '<tr><td>'
                row2 = ['' for j in range(len(row))]
                row2[idx_lap] = str(row[idx_lap][i])
                entry += '</td><td>'.join(row2) + '</tr>\n'
        return entry