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


import asmmobile.util as util
import csv
import datetime
import dateutil.tz
import re

def normalizeShortNameEn(name):
    result = name.replace("ARTtech seminars - ", "Seminar, ")
    result = result.replace("ARTtech seminars: ", "Seminar: ")
    return result

def normalizeShortNameFi(name):
    result = name.replace("ARTtech seminars - ", "Seminaari, ")
    result = result.replace("ARTtech seminars: ", "Seminaari: ")
    return result

def parseCsvDate(dateString):
    # Date is in format:
    # Mon 14.7.09 18:00
    dayName, date, time = dateString.split(" ")
    day, month, year = (int(x) for x in date.split("."))
    hour, minute = (int(x) for x in time.split(":"))

    offset = util.tzOffsetString(
        datetime.datetime.now(dateutil.tz.tzlocal()).utcoffset())

    return "%04d-%02d-%02dT%02d:%02d:%02d%s" % (
        (2000 + year), month, day, hour, minute, 0, offset)

def escapeDescription(description):
    escaped = description
    escaped = escaped.replace("> ", "> <!---->")
    escaped = escaped.replace(" <", " <!----><")
    # Common mistake where & is not escaped in descriptions.
    escaped = re.sub("& ", "&amp; ", escaped)
    return escaped


def importer(filename, prefix):
    # Schedule is in format:
    # FIELDNAME1;FIELDNAME2;...
    # field_value1;field_value2;...
    fields = "ID;Outline_Number;Name;Duration;Start_Date;Finish_Date;AsmTV;BigScreen;Major;Public;SumTask;Class;URL;Title_EN;Title_FI;Location_EN;Location_FI;Location_URL;Outline_Level;Description_EN;Description_FI;Cancelled".split(";")
    fp = open(filename, "r")
    dialect = csv.Sniffer().sniff(fp.read(), delimiters="\t;")
    fp.seek(0)
    reader = csv.DictReader(fp, fieldnames=fields, dialect=dialect)

    # Skip over header line.
    reader.next()

    locations = {}
    events = {}

    for lang in ['en', 'fi']:
        if lang not in locations:
            locations[lang] = {}
        if lang not in events:
            events[lang] = {}

    order_id = 0
    for entry in reader:
        if entry['Public'].lower() == 'no':
            continue
        # Ignore empty entries:
        if entry['Title_EN'] == "" or entry['Title_FI'] == "":
            continue

        locationKey = util.convertNameToKey(entry['Location_EN'])

        locationUrl = entry['Location_URL']
        # Add absolute URL to main website if location is relative
        if not locationUrl.startswith("http"):
            locationUrl = "http://www.assembly.org%s" % locationUrl

        startTime = parseCsvDate(entry['Start_Date'])
        eventId = "%s%s-%s" % (prefix, startTime[0:4], entry['ID'])
        categories = []
        isMajor = False
        if entry['Major'].lower() == 'yes':
            isMajor = True
            categories.append("Major_event")
        if len(entry['Class']) > 0:
            categories += entry['Class'].split(" ")

        url = entry['URL']
        # Add absolute URL to main website if location is relative
        if not url.startswith("http"):
            url = "http://www.assembly.org%s" % url

        if locationKey == '':
            locationKey = None
        else:
            locations['en'][locationKey] = {
                'name': unicode(entry['Location_EN'], 'utf-8'),
                'url': locationUrl,
                }
            locations['fi'][locationKey] = {
                'name': unicode(entry['Location_FI'], 'utf-8'),
                'url': locationUrl,
                }

        events['en'][eventId] = {
            'name': unicode(entry['Title_EN'], 'utf-8'),
            'url': url,
            'start': startTime,
            'end': parseCsvDate(entry['Finish_Date']),
            'location': locationKey,
            'categories': categories,
            'is-major': isMajor,
            'description': escapeDescription(unicode(entry['Description_EN'], 'utf-8')),
            'canceled': (entry['Cancelled'].lower() == 'yes'),
            'order': order_id,
            'short-name': normalizeShortNameEn(unicode(entry['Title_EN'], 'utf-8')),
            }
        events['fi'][eventId] = {
            'name': unicode(entry['Title_FI'], 'utf-8'),
            'url': url,
            'start': startTime,
            'end': parseCsvDate(entry['Finish_Date']),
            'location': locationKey,
            'categories': categories,
            'is-major': isMajor,
            'description': escapeDescription(unicode(entry['Description_FI'], 'utf-8')),
            'canceled': (entry['Cancelled'].lower() == 'yes'),
            'order': order_id,
            'short-name': normalizeShortNameFi(unicode(entry['Title_FI'], 'utf-8')),
            }
        order_id += 1

    return locations, events
