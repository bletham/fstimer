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

'''Printing infrastructure for the fsTimer package'''

class Printer(object):
    '''Base class for an fstimer printer.
       Defines an API for implementation of real printers'''

    def __init__(self, fields, categories, print_place):
        '''constructor
           @type fields: list
           @param fields: fields of the output
           @type categories: list
           @param categories: existing categories
           @type print_place: boolean
           @param print_place: print place'''
        self.fields = fields
        self.categories = categories
        self.print_place = print_place
        self.place = 1
        self.cat_place = {cat:1 for cat in self.categories}
        self.row_start = ''
        self.row_delim = ''
        self.row_end = ''

    def file_extension(self):
        '''returns the file extension to be used for files
           containing data from this printer'''
        return ''

    def header(self):
        '''Returns the header of the printout'''
        return ''

    def footer(self):
        '''Returns the footer of the printout'''
        return ''

    def scratch_table_header(self):
        '''Returns the header of the printout for scratch results'''
        return ''

    def scratch_table_footer(self):
        '''Returns the header of the printout for scratch results'''
        return ''

    def cat_table_header(self, category):
        '''Returns the header of the printout for results by category.
           @type category: string
           @param category: name of the category handled by the table'''
        return ''

    def cat_table_footer(self, category):
        '''Returns the footer of the printout for results by category.
           @type category: string
           @param category: name of the category handled by the table'''
        return ''
    
    def common_entry(self, row):
        return self.row_delim.join(row)

    def scratch_entry(self, row, category=None):
        '''Returns the printout of the entry of a given runner
           in the scratch results'''
        return (self.row_start + self.get_place_str(category) +
                self.common_entry(row) + self.row_end)

    def get_place_str(self, category):
        if not self.print_place:
            return ''
        if category is None:
            place = str(self.place)
            self.place += 1
        else:
            place = str(self.cat_place[category])
            self.cat_place[category] += 1
        return place + self.row_delim
