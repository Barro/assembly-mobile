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

import random
import datetime
import dateutil.tz

parts = """a e i u o y
ca ce ci cu co cy
na ne ni nu no ny
za ze zi zu zo zy
gha ghe ghi ghu gho ghy
ta te ti tu to ty
ma me mi mu mo my
va ve vi vu vo vy""".split()

def generateName():
    words = []
    for wid in xrange(0, random.randint(1, 3)):
        word = ""
        for part in xrange(0, random.randint(2, 4)):
            word += parts[random.randint(0, len(parts) - 1)]
        words.append(word)
    name = " ".join(words)
    return name[0].upper() + name[1:]

def generateLanguageData(events, locations, startTime):
    locationNames = []
    resultLocations = {}
    for locationId  in xrange(0, locations):
        name = generateName()
        idName = name.replace(" ", "_").lower()
        resultLocations[name] = "http://www.example.com/location/%s" % idName
        locationNames.append(name)

    lengths = [datetime.timedelta(minutes=minutes) for minutes in
               [0, 15, 30, 30, 45, 60, 60, 60, 60, 60, 90, 90, 90, 120, 120]]

    increases = [datetime.timedelta(minutes=minutes) for minutes in
                 [15, 30, 30, 30, 30, 30, 30, 30, 60, 60, 60]]

    now = datetime.datetime(2009, 1, 1).now(dateutil.tz.tzlocal())
    # Start from full hour.
    eventTime = now - datetime.timedelta(
        seconds=now.second, minutes=now.minute)

    resultEvents = {}
    currentEvents = 1
    for id in xrange(0, events):
        eventName = generateName()
        eventId = "%d_%s" % (id, eventName.replace(" ", "_").lower())
        resultEvents[eventId] = {
            'name': eventName,
            'start': eventTime,
            'end': eventTime + lengths[random.randint(0, len(lengths) - 1)],
            'location': locationNames[random.randint(0, len(locationNames) - 1)],
            'categories': [],
            'is-major': random.random() < 0.1,
            }

        if currentEvents >= 6:
            increaseTime = True
        else:
            increaseTime = random.random() < 0.4

        if increaseTime:
            eventTime += increases[random.randint(0, len(increases) - 1)]
            currentEvents = 1
        else:
            currentEvents += 1
    return (resultLocations, resultEvents)

def importer(events, locations, languages=['en'], startTime='now'):
    resultLocations = {}
    resultEvents = {}
    for language in languages:
        resultLocations[language], resultEvents[language] = generateLanguageData(events, locations, startTime)

    return (resultLocations, resultEvents)
