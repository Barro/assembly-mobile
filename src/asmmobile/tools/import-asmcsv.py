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


import csv
import datetime
import dateutil.tz

def parseCsvDate(dateString):
    # Date is in format:
    # Mon 14.7.09 18:00
    dayName, date, time = dateString.split(" ")
    day, month, year = (int(x) for x in date.split("."))
    hour, minute = (int(x) for x in time.split(":"))
    return datetime.datetime(
        year=(2000 + year),
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        tzinfo=dateutil.tz.tzlocal()
        )


def importer(filename, prefix, language):
    # Schedule is in format:
    # FIELDNAME1;FIELDNAME2;...
    # field_value1;field_value2;...
    fp = open(filename, "r")
    reader = csv.DictReader(fp, delimiter=';')
    locations = {}
    events = {}
    for entry in reader:
        if entry['Public'] == 'No':
            continue
        # Ignore empty entries:
        if entry['Title_' + language] == "":
            continue
        locationName = entry['Location_' + language]
        locationUrl = entry['Location_URL']
        # Add absolute URL to main website if location is relative
        if not locationUrl.startswith("http"):
            locationUrl = "http://www.assembly.org%s" % locationUrl

        locations[locationName] = locationUrl
        startTime = parseCsvDate(entry['Start_Date'])
        eventId = "%s%d_%s" % (prefix, startTime.year, entry['ID'])
        categories = []
        isMajor = False
        if entry['Major'] == 'Yes':
            isMajor = True
            categories.append("Major_event")
        if len(entry['Class']) > 0:
            categories += entry['Class'].split(" ")

        url = entry['URL']
        # Add absolute URL to main website if location is relative
        if not url.startswith("http"):
            url = "http://www.assembly.org%s" % url

        events[eventId] = {
            'name': entry['Title_' + language],
            'url': url,
            'start': startTime,
            'end': parseCsvDate(entry['Finish_Date']),
            'location': locationName,
            'categories': categories,
            'is-major': isMajor,
            }
    return (locations, events)
