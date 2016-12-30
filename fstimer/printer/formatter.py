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

"""
Format results for printing
"""

import os
from fstimer.printer.printcsv import CSVPrinter
from fstimer.printer.printcsvlaps import CSVPrinterLaps
from fstimer.printer.printhtml import HTMLPrinter
from fstimer.printer.printhtmllaps import HTMLPrinterLaps
from collections import defaultdict
from fstimer.time_ops import time_format, time_parse, time_diff

def print_times(pytimer, use_csv):
    '''print times to files'''
    # choose the right Printer Class
    if use_csv:
        if pytimer.numlaps > 1:
            printer_class = CSVPrinterLaps
        else:
            printer_class = CSVPrinter
    else:
        if pytimer.numlaps > 1:
            printer_class = HTMLPrinterLaps
        else:
            printer_class = HTMLPrinter
    # Figure out what the columns will be.
    cols = []
    # Prefer first time, and then pace, if they are in the printfields
    for field in ['Time', 'Pace']:
        if field in pytimer.printfields:
            cols.append(field)
    if pytimer.numlaps > 1 and 'Time' in pytimer.printfields:
        cols.append('Lap Times')
    # Then add in the calculated fields
    for field in pytimer.printfields:
        if not field in ['Time', 'Pace'] and not field in pytimer.fields:
            cols.append(field)  # A computed field
    # Finally registration fields
    for field in pytimer.fields:
        if field in pytimer.printfields:
            cols.append(field)
    # Prepare functions for computing each column
    col_fns = []
    for col in cols:
        if col == 'Lap Times':
            text = 'lap_time'
        else:
            text = pytimer.printfields[col]
            # Sub {Time}
            text = text.replace('{Time}', 'time_parse(time).total_seconds()')
            # Age
            text = text.replace('{Age}', "int(userdata['Age'])")
            # ID
            text = text.replace('{ID}', "tag")
            # And the other registration fields
            for field in pytimer.fields:
                if field not in ['Age', 'ID']:
                    text = text.replace('{' + field + '}',
                                        "userdata['{}']".format(field))
        col_fns.append(text)
    # Get the list of different things we will rank by
    ranking_keys = set(pytimer.rankings.values())
    # instantiate the printer
    printer = printer_class(cols, [div[0] for div in pytimer.divisions])
    # Build the results
    scratchresults = printer.scratch_table_header()
    divresults = {div[0]:'\n'+printer.cat_table_header(div[0])
                    for div in pytimer.divisions}
    # Do the ranking for each ranking key
    ranked_results = {}
    for ranking_key in ranking_keys:
        rank_indx = cols.index(ranking_key)
        ranked_results = get_sorted_results(
            pytimer.projecttype, pytimer.passid, pytimer.numlaps,
            pytimer.timing, pytimer.rawtimes, rank_indx, cols, col_fns)
        for tag, row in ranked_results:
            # Add this to the appropriate results
            if pytimer.rankings['Overall'] == ranking_key:
                scratchresults += printer.scratch_entry(row)
            mydivs = get_divisions(pytimer.timing, tag, pytimer.divisions)
            for div in mydivs:
                if pytimer.rankings[div] == ranking_key:
                    divresults[div] += printer.cat_entry(div, row)
    scratchresults += printer.scratch_table_footer()
    for div in divresults:
        divresults[div] += printer.cat_table_footer(div)
    # now save to files
    scratch_file = os.path.join(
        pytimer.path, '_'.join(
            [os.path.basename(pytimer.path),
             pytimer.timewin.timestr,
             'alltimes.' + printer.file_extension()]))
    with open(scratch_file, 'w') as scratch_out:
        scratch_out.write(printer.header())
        scratch_out.write(scratchresults)
        scratch_out.write(printer.footer())
    div_file = os.path.join(
        pytimer.path, '_'.join(
            [os.path.basename(pytimer.path),
             pytimer.timewin.timestr,
             'divtimes.' + printer.file_extension()]))
    with open(div_file, 'w') as div_out:
        div_out.write(printer.header())
        for div in pytimer.divisions:
            div_out.write(divresults[div[0]])
        div_out.write(printer.footer())

def get_divisions(timing, tag, divisions):
    '''Get the divisions for a given timing entry'''
    try:
        age = int(timing[tag]['Age'])
    except ValueError:
        age = ''
    mydivs = []
    # go through the divisions
    for div in divisions:
        # check all fields
        for field in div[1]:
            if field == 'Age':
                if not age or age < div[1]['Age'][0] or age > div[1]['Age'][1]:
                    break
            else:
                if timing[tag][field] != div[1][field]:
                    break
        else:
            mydivs.append(div[0])
    return mydivs

def get_sync_times_and_ids(rawtimes):
    '''returns a list of ids and a list of timedeltas that are
        "synced", that is that have the same number of entries.
        Entries without a counterpart are dropped'''
    #Note that the newest entries are at the _start_ of the rawtimes lists
    offset = len(rawtimes['times']) - len(rawtimes['ids'])
    if offset < 0:
        adj_ids = rawtimes['ids'][-offset:]
        adj_times = list(rawtimes['times'])
    elif offset > 0:
        adj_ids = list(rawtimes['ids'])
        adj_times = rawtimes['times'][offset:]
    else:
        adj_ids = list(rawtimes['ids'])
        adj_times = list(rawtimes['times'])
    return adj_ids, adj_times

def get_sorted_results(projecttype, passid, numlaps, timing, rawtimes,
                       rank_indx, cols, col_fns):
    '''returns a sorted list of (id, result) items.
        The content of result depends on the race type'''
    # get raw times
    timeslist = zip(*get_sync_times_and_ids(rawtimes))
    #Handle blank times, and handicap correction
    # Handicap correction
    if projecttype == 'handicap':
        new_timeslist = []
        for tag, time in timeslist:
            if tag and time and tag != passid:
                try:
                    new_timeslist.append(
                        (tag, time_diff(time, timing[tag]['Handicap'])))
                except AttributeError:
                    # time or Handicap couldn't be converted to timedelta
                    new_timeslist.append((tag, '_'))
            # Else: drop entries with blank tag, blank time, or pass ID
        timeslist = list(new_timeslist) #replace
    else:
        #Drop times that are blank or have the passid
        timeslist = [(tag, time) for tag, time in timeslist
                     if tag and time and tag != passid]
    # Compute lap times, if a lap race
    if numlaps > 1:
        # multi laps - groups times by tag
        # Each value of laptimesdic is a list, sorted in order from
        # fastest time (1st lap) to longest time (last lap).
        timeslist_sorted = []
        for (tag, time) in timeslist:
            try:
                timeslist_sorted.append((tag, time_parse(time)))
            except AttributeError:
                pass
        timeslist_sorted = sorted(timeslist_sorted, key=lambda x: x[1])
        laptimesdic = defaultdict(list)
        for (tag, time) in timeslist_sorted:
            laptimesdic[tag].append(time_format(time.total_seconds()))
        # compute the lap times.
        lap_times = {}
        total_times = {}
        for tag in laptimesdic:
            # First put the total race time
            if len(laptimesdic[tag]) == numlaps:
                total_times[tag] = laptimesdic[tag][-1]
            else:
                total_times[tag] = '_'
            # And the first lap
            lap_times[tag] = ['1 - ' + laptimesdic[tag][0]]
            # And now the subsequent laps
            for ii in range(len(laptimesdic[tag])-1):
                try:
                    lap_times[tag].append(
                        '{} - {}'.format(
                            ii + 2,
                            time_diff(laptimesdic[tag][ii+1],
                                      laptimesdic[tag][ii])))
                except AttributeError:
                    lap_times[tag].append(str(ii+2) + ' - _')
        # Now correct timeslist to have the new total times
        timeslist = list(total_times.items())
    else:
        lap_times = defaultdict(int)
    # Compute each results row
    result_rows = []
    for tag, time in timeslist:
        row = []
        lap_time = lap_times[tag]
        userdata = timing[tag]
        for i, col_fn in enumerate(col_fns):
            try:
                row.append((eval(col_fn)))
            except (SyntaxError, TypeError, AttributeError, ValueError):
                if cols[i] == 'ID':
                    row.append(tag)
                else:
                    row.append(None)
        result_rows.append((tag, row))
    # sort by column rank_indx.
    # Try sorting as float, but if that doesn't work, use string.
    try:
        # Define a sorter that will handle the Nones
        def floatsort(x):
            if x[1][rank_indx] is None:
                return 1e20
            else:
                return x[1][rank_indx]
        result_rows = sorted(result_rows, key=floatsort)
    except TypeError:
        def stringsort(x):
            if x[1][rank_indx] is None:
                return ''
            else:
                return x[1][rank_indx]
        result_rows = sorted(result_rows, key=stringsort)
    # Remove duplicate entries: If a tag has multiple entries, keep only the
    # most highly ranked. Also replace total times and pace times with
    # formatted times, stringify everything but Lap Times, and replace Nones.
    indx_format_time = []
    for field in ['Time', 'Pace']:
        if field in cols:
            indx_format_time.append(cols.index(field))
    taglist = set()
    result_rows_dedup = []
    for tag, row in result_rows:
        if tag in taglist:
            pass  # drop it
        else:
            taglist.add(tag)
            row_new = []
            for i, val in enumerate(row):
                if val is None:
                    if i == rank_indx:
                        val = '_'
                    else:
                        val = ''
                elif cols[i] in ['Time', 'Pace']:
                    val = time_format(val)
                elif cols[i] == 'Lap Times':
                    pass  # Leave it as is
                else:
                    val = str(val)
                row_new.append(val)
            result_rows_dedup.append((tag, row_new))
    return result_rows_dedup
