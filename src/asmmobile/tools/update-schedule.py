#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Assembly mobile - mobile content for visitors of Assembly computer festival.
# Copyright (C) 2009  Jussi Judin
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


import zope.app.component.hooks
import zope.component
import transaction

import sys
import csv
import datetime

import asmmobile.event

(scriptname, sitename, scheduleFile, lang) = sys.argv

# Set the site so that events and utilities are registered correctly
app = root[sitename]
zope.app.component.hooks.setSite(app)

def parseDate(dateString):
    # Date is in format:
    # Mon 14.7.09 18:00
    dayName, date, time = dateString.split(" ")
    day, month, year = (int(x) for x in date.split("."))
    hour, minute = (int(x) for x in time.split(":"))
    return datetime.datetime(2000 + year, month, day, hour, minute)


def parseCsv(filename, lang):
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
        if entry['Title_' + lang] == "":
            continue
        locationName = entry['Location_' + lang]
        locationUrl = entry['Location_URL']
        locations[locationName] = locationUrl
        startTime = parseDate(entry['Start_Date']),
        eventId = "asm%d_%s" % (startTime.year, entry['ID'])
        categories = []
        if entry['Major'] == 'Yes':
            categories.append("Major_event")
        if len(entry['Class']) > 0:
            categories += entry['Class'].split(" ")
        events[eventId] = {'name': entry['Title_' + lang],
                           'url': entry['URL'],
                           'start': startTime,
                           'end': parseDate(entry['Finish_Date']),
                           'location': locationName,
                           'categories': categories,
                           }
    return (locations, events)

locations, events = parseCsv(scheduleFile, lang)

for name,url in locations.items():
    app.addLocation(name, url, None, None, None)


app.updateEvents(events)

transaction.commit()
