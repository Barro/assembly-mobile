#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Assembly mobile - mobile content for visitors of Assembly computer festival.
# Copyright (C) 2009  Assembly Organizing
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3 of the
# License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import icalendar
import dateutil.tz

def importer(locations, events, filename, prefix='', locationMap={}, majorCategory=None):
    calFp = open(filename, "r")
    cal = icalendar.Calendar.from_string(calFp.read())
    calFp.close()

    for event in cal.walk('vevent'):
        id = event.decoded('uid')
        start = event.decoded('DTSTART').replace(tzinfo=dateutil.tz.tzlocal())
        end = event.decoded('DTEND').replace(tzinfo=dateutil.tz.tzlocal())
        categories = event.decoded('CATEGORIES').split(" ")
        url = event.decoded('URL', u'')
        name = event.decoded('SUMMARY', u'')

        location = event.decoded('LOCATION', u'')
        if location in locationMap:
            location = locationMap[location]

        locations[location] = ""

        isMajor = majorCategory in categories

        events[id] = {'name': name,
                      'start': start,
                      'end': end,
                      'url': url,
                      'location': location,
                      'categories': categories,
                      'is-major': isMajor,
                      }

    return locations, events


