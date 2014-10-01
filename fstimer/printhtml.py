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

'''Printer class for html files for single lap races'''

import fstimer.printer

class HTMLPrinter(fstimer.printer.Printer):
    '''Printer class for html files for single lap races'''

    def __init__(self, fields, categories):
        '''constructor
           @type fields: list
           @param fields: fields of the output
           @type categories: list
           @param categories: existing categories'''
        super(HTMLPrinter, self).__init__(fields, categories)
        self.place = 1
        self.cat_place = {cat:1 for cat in self.categories}

    def file_extension(self):
        '''returns the file extension to be used for files
           containing data from this printer'''
        return 'html'

    def header(self):
        '''Returns the header of the printout'''
        return '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <style type="text/css">
        #tab
        {
              font-family: Sans-Serif;
              font-size: 14px;
              margin: 20px;
              width: 650px;
              text-align: left;
        }
        #tab th
        {
              font-size: 15px;
              font-weight: bold;
              padding: 10px 8px;
              border-bottom: 2px solid gray;
        }
        #tab td
        {
              border-bottom: 1px solid #ccc;
              padding: 6px 8px;
        }
        #footer{ margin-top: 20px; margin-left: 20px; font: 10px sans-serif;}
        </style>
        </head>
        <body>
'''

    def footer(self):
        '''Returns the footer of the printout'''
        return '<div id="footer">Race timing with fsTimer - free, open source software for race timing. http://fstimer.org</div></body></html>'

    def scratch_table_header(self):
        '''Returns the header of the printout for scratch results'''
        header = '<table id="tab"> <thead> <tr>\n'
        for field in self.fields:
            header += '<th scope="col">' + field + '</th>\n'
        header += '</tr> </thead> <tbody>\n'
        return header

    def scratch_table_footer(self):
        '''Returns the header of the printout for scratch results'''
        return '</tbody></table>'

    def cat_table_header(self, category):
        '''Returns the header of the printout for results by category.
           @type category: string
           @param category: name of the category handled by the table'''
        return '<span style="font-size:22px">' + category + '</span>\n' + \
               self.scratch_table_header()

    def cat_table_footer(self, category):
        '''Returns the footer of the printout for results by category.
           @type category: string
           @param category: name of the category handled by the table'''
        return self.scratch_table_footer()

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
        data = [str(timing_data),
                runner_data['First name'] + ' '+ runner_data['Last name'],
                bibid,
                runner_data['Gender'],
                str(runner_data['Age'])]
        for field in self.fields[6:]:
            data.append(runner_data[field])
        return '</td><td>'.join(data)+'</td></tr>\n'

    def scratch_entry(self, bibid, timing_data, runner_data):
        '''Returns the printout of the entry of a given runner
           in the scratch results
           @type bibid: string
           @param bibid: the bibid of the runner
           @type timing_data: timedelta|list
           @param timing_data: timing data for the runner. May be his/her time
                               or a list of times for multi lap races
           @type runner_data: dict
           @param runner_data: data concerning the runner. A dictionnary
                               of field name / field value'''
        result = '<tr><td>' + str(self.place) + '</td><td>' + self.common_entry(bibid, timing_data, runner_data)
        self.place += 1
        return result

    def cat_entry(self, bibid, category, timing_data, runner_data):
        '''Returns the printout of the entry of a given runner
           in the divisional results
           @type bibid: string
           @param bibid: the bibid of the runner
           @type category: string
           @param category: name of the category for this runner
           @type timing_data: timedelta|list
           @param timing_data: timing data for the runner. May be his/her time
                               or a list of times for multi lap races
           @type runner_data: dict
           @param runner_data: data concerning the runner. A dictionnary
                               of field name / field value'''
        result = '<tr><td>' + str(self.cat_place[category]) + '</td><td>' + self.common_entry(bibid, timing_data, runner_data)
        self.cat_place[category] += 1
        return result
