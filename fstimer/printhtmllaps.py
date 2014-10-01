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

    def common_entry(self, bibid, timing_data, runner_data):
        '''Returns the common part of the printout of the entry
           of a given runner for scratch or by category results
           @type bibid: string
           @param bibid: the bibid of the runner
           @type timing_data: timedelta|list
           @param timing_data: timing data for the runner. May be his/her time
                               or a list of times for multi lap races
           @type runner_data: dict
           @param runner_data: data concerning the runner. A dictionnary
                               of field name / field value'''
        # first line, with total time and first lap
        data = [str(timing_data[0]),
                '1 - ' + str(timing_data[1]),
                runner_data['First name'] + ' '+ runner_data['Last name'],
                bibid,
                runner_data['Gender'],
                str(runner_data['Age'])]
        for field in self.fields[7:]:
            data.append(runner_data[field])
        entry = '</td><td>'.join(data)+'</td></tr>\n'
        # others lines, with other lap times
        for i in range(2, len(timing_data)):
            data = ['', '', str(i) + ' - ' + str(timing_data[i]), '', '', '', '']
            data.extend(['']*(len(self.fields)-7))
            entry += '<tr><td>' + '</td><td>'.join(data) + '</td></tr>\n'
        return entry
