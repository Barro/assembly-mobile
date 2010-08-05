#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Assembly mobile - mobile content for visitors of Assembly computer festival.
# Copyright (C) 2010  Assembly Organizing
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

import xml.etree.ElementTree as etree
import asmmobile.util as util
import datetime
import dateutil.tz

def importer(filename, prefix='elaine-'):
    events = {}
    locations = {}
    root = etree.parse(filename).getroot()
    offset = util.tzOffsetString(
        datetime.datetime.now(dateutil.tz.tzlocal()).utcoffset())
    for entry in root.getiterator('entry'):
        eventId = prefix + entry.attrib['id']
        titles = {}
        descriptions = {}
        for title in entry.getiterator('title'):
            language = title.attrib['lang']
            titles[language] = title.text
        for description in entry.getiterator('description'):
            if description is None:
                continue
            language = description.attrib['lang']
            descriptions[language] = description.text
        start = entry.find('start_at').text
        end = entry.find('end_at').text
        for language, title in titles.items():
            if language not in events:
                events[language] = {}
                locations[language] = {'assemblytv': {'name': u'AssemblyTV'}}
            event = {
                'name': title,
                'start': start + offset,
                'end': end + offset,
                'location': 'assemblytv',
                'url': u'http://www.assemblytv.net/',
                }
            if language in descriptions:
                event['description'] = descriptions[language]
            events[language][eventId] = event
    return locations, events
