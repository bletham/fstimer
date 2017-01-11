#!/usr/bin/env python3

#fsTimer - free, open source software for race timing.
#Copyright 2012-17 Ben Letham

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

'''Printer class for csv files for single lap races'''

import os
from fstimer.printer.printer import Printer

class CSVPrinter(Printer):
    '''Printer class for csv files for single lap races'''

    def __init__(self, fields, categories, print_place):
        '''constructor
           @type fields: list
           @param fields: fields of the output
           @type categories: list
           @param categories: existing categories'''
        super(CSVPrinter, self).__init__(fields, categories, print_place)
        self.row_start = ''
        self.row_delim = ','
        self.row_end = '\n'

    def file_extension(self):
        '''returns the file extension to be used for files
           containing data from this printer'''
        return 'csv'

    def scratch_table_header(self):
        '''Returns the header of the printout for scratch results'''
        return 'Place,' + ','.join(self.fields) + '\n'

    def cat_table_header(self, category):
        '''Returns the header of the printout for results by category.
           @type category: string
           @param category: name of the category handled by the table'''
        return category + '\n' + self.scratch_table_header()

    def cat_table_footer(self, category):
        '''Returns the footer of the printout for results by category.
           @type category: string
           @param category: name of the category handled by the table'''
        return '\n'
