#!/usr/bin/env python

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

'''Printer class for csv files for single lap races'''

import os
import fstimer.printer

class CSVPrinter(fstimer.printer.Printer):
    '''Printer class for csv files for single lap races'''

    def __init__(self, fields, categories):
        '''constructor
           @type fields: list
           @param fields: fields of the output
           @type categories: list
           @param categories: existing categories'''
        super(CSVPrinter, self).__init__(fields, categories)
        self.place = 1
        self.cat_place = {cat:1 for cat in self.categories}

    def file_extension(self):
        '''returns the file extension to be used for files
           containing data from this printer'''
        return 'csv'

    def scratch_table_header(self):
        '''Returns the header of the printout for scratch results'''
        return ','.join(self.fields) + os.linesep

    def cat_table_header(self, category):
        '''Returns the header of the printout for results by category.
           @type category: string
           @param category: name of the category handled by the table'''
        return category + '\n' + self.scratch_table_header()

    def common_entry(self, bibid, timing_data, runner_data):
        '''Returns the common part of the printout of the entry
           of a given runner for scratch or by category results
           @type bibid: string
           @param bibid: the bibid of the runner
           @type timing_data: str|list
           @param timing_data: timing data for the runner. May be his/her time
                               or a list of times for multi lap races
           @type runner_data: dict
           @param runner_data: data concerning the runner. A dictionnary
                               of field name / field value'''
        data = [timing_data,
                runner_data['First name'] + ' '+ runner_data['Last name'],
                bibid,
                runner_data['Gender'],
                runner_data['Age']]
        for field in self.fields[6:]:
            data.append(runner_data[field])
        return ','.join(data) + '\n'

    def scratch_entry(self, bibid, timing_data, runner_data):
        '''Returns the printout of the entry of a given runner
           in the scratch results
           @type bibid: string
           @param bibid: the bibid of the runner
           @type timing_data: str|list
           @param timing_data: timing data for the runner. May be his/her time
                               or a list of times for multi lap races
           @type runner_data: dict
           @param runner_data: data concerning the runner. A dictionnary
                               of field name / field value'''
        result = str(self.place) + ',' + self.common_entry(bibid, timing_data, runner_data)
        self.place += 1
        return result

    def cat_entry(self, bibid, category, timing_data, runner_data):
        '''Returns the printout of the entry of a given runner
           in the divisional results
           @type bibid: string
           @param bibid: the bibid of the runner
           @type category: string
           @param category: name of the category for this runner
           @type timing_data: str|list
           @param timing_data: timing data for the runner. May be his/her time
                               or a list of times for multi lap races
           @type runner_data: dict
           @param runner_data: data concerning the runner. A dictionnary
                               of field name / field value'''
        result = str(self.cat_place[category]) + ',' + self.common_entry(bibid, timing_data, runner_data)
        self.cat_place[category] += 1
        return result
