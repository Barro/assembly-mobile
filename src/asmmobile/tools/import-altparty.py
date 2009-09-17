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


import xml.etree.ElementTree as etree
import dateutil.parser
import datetime

def importer(filename, prefix):
    events = {}
    locations = {}
    for event in etree.parse(filename).getroot():
        if event.find("public").text != "true":
            continue
        id = prefix + event.find("id").text
        start = dateutil.parser.parse(event.find("start-at").text)
        end = start + \
            datetime.timedelta(minutes=int(event.find("duration").text))
        location = event.find("location").text
        description = event.find("description").text
        events[id] = {'name': event.find("title").text,
                      'start': start,
                      'end': end,
                      'location': location,
                      'description': description,
                      'url': '',
                      'categories': [],
                      }
        locations[location] = ""

    return (locations, events)

