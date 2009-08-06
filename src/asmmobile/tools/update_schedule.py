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


import zope.app.component.hooks
import zope.component
import transaction
import icalendar

import sys
import csv
import datetime

def importIcalEvents(filename, locationMap={}):
    calFp = open(filename, "r")
    cal = icalendar.Calendar.from_string(calFp.read())
    calFp.close()

    locations = {}
    events = {}
    for event in cal.walk('vevent'):
        id = event.decoded('uid')
        start = event.decoded('DTSTART')
        end = event.decoded('DTEND')
        categories = event.decoded('CATEGORIES').split(" ")
#         url = event.decoded('URL')
        url = u''
        name = event.decoded('SUMMARY')

        location = event.decoded('LOCATION')
        if location in locationMap:
            location = locationMap[location]

        locations[location] = ""

        events[id] = {'name': name,
                      'start': start,
                      'end': end,
                      'url': url,
                      'location': location,
                      'categories': categories,
                      }

    return (locations, events)


def parseCsvDate(dateString):
    # Date is in format:
    # Mon 14.7.09 18:00
    dayName, date, time = dateString.split(" ")
    day, month, year = (int(x) for x in date.split("."))
    hour, minute = (int(x) for x in time.split(":"))
    return datetime.datetime(2000 + year, month, day, hour, minute)


def parseCsv(filename, language, prefix):
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
        if entry['Major'] == 'Yes':
            categories.append("Major_event")
        if len(entry['Class']) > 0:
            categories += entry['Class'].split(" ")

        url = entry['URL']
        # Add absolute URL to main website if location is relative
        if not url.startswith("http"):
            url = "http://www.assembly.org%s" % url

        events[eventId] = {'name': entry['Title_' + language],
                           'url': url,
                           'start': startTime,
                           'end': parseCsvDate(entry['Finish_Date']),
                           'location': locationName,
                           'categories': categories,
                           }
    return (locations, events)


IMPORTERS = {'asmtv': importIcalEvents,
             'asm': parseCsv}

MAPPING_LOCATIONS = {'Big screen': 'MAIN-ARENA',
                     'Stage': 'MAIN-ARENA',
                     }


PRIORITIES = {'MAIN-ARENA': 10,
              'Seminar hall': 9,
              'Game hall': 7,
              'PMS': 6,
              'AssemblyTV': 4,
              'Infodesk': -1,
              }

def updateSchedule(app, scheduleImports):
    for importerName in scheduleImports.keys():
        if importerName not in IMPORTERS:
            raise Exception("No %s in schedule reader handlers" % importerName)

    locations = {}
    events = {}

    for importerName, params in scheduleImports.items():
        importer = IMPORTERS[importerName]
        importedLocations, importedEvents = importer(**params)
        for name, url in importedLocations.items():
            locations[name] = url

        for eventId, eventParams in importedEvents.items():
            if eventId in events:
                raise Exception("Duplicate event ID: %s (%s)" % \
                                    (eventId, eventParams))
            events[eventId] = eventParams

    mappingLocations = {}
    for fromLocation, toLocation in MAPPING_LOCATIONS.items():
        app.addLocation(toLocation, None, None, None, None)
        app.addLocation(fromLocation, None, None, None, toLocation)
        locations[toLocation] = None

    zope.app.component.hooks.setSite(app)
    for name,url in locations.items():
        priority = None
        if name in PRIORITIES:
            priority = PRIORITIES[name]
        app.addLocation(name, url, priority, None, None)

    app.updateEvents(events)
    transaction.commit()
