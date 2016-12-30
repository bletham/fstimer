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

import datetime
import re

def time_format(t):
    '''formats time for display in the timing window'''
    milli = int((t - int(t)) * 10)
    hours, rem = divmod(int(t), 3600)
    minutes, seconds = divmod(rem, 60)
    if hours > 0:
        s = '%d:%02d:%02d.%01d' % (hours, minutes, seconds, milli)
    else:
        s = '%d:%02d.%01d' % (minutes, seconds, milli)
    return s

def time_parse(dt):
    '''converts string time to datetime.timedelta'''
    if dt and dt[0] == '-':
        return datetime.timedelta(0) #we don't allow negative times
    d = re.match(r'((?P<hours>\d+):)?(?P<minutes>\d+):(?P<seconds>\d+)(\.(?P<milliseconds>\d+))?', dt).groupdict(0)
    d['milliseconds'] = int(d['milliseconds'])*100  # they are actually centiseconds in the string
    return datetime.timedelta(**dict(((key, int(value)) for key, value in d.items())))

def time_diff(t1, t2):
    '''takes the diff of two string times and returns it as a time, rectified to 0. t1-t2.'''
    delta_t = time_parse(t1) - time_parse(t2)
    if delta_t < datetime.timedelta(0):
        return '0:00.0'
    else:
        return time_format(delta_t.total_seconds())

def time_sum(t1, t2):
    '''takes the sum of two string times and returns it as a time, t1+t2.'''
    timesum = time_parse(t1) + time_parse(t2)
    return time_format(timesum.total_seconds())
